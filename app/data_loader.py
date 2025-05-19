from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType
from pyspark.sql.functions import col, to_timestamp
import pandas as pd
from abc import ABC, abstractmethod


class AbstractSBBDataLoader(ABC):
    @abstractmethod
    def load_istdaten(self, path: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def load_didok(self, path: str, valid_bpuics=None) -> pd.DataFrame:
        pass


class PandasSBBDataLoader(AbstractSBBDataLoader):
    def load_istdaten(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path, sep=";", low_memory=False)
        df = df[(df["PRODUKT_ID"] == "Zug") & (df["FAELLT_AUS_TF"] == False)]
        df["BPUIC"] = df["BPUIC"].astype(int)

        # Correct date parsing
        datetime_format = "%d.%m.%Y %H:%M"
        df['ANKUNFTSZEIT'] = pd.to_datetime(df['ANKUNFTSZEIT'], format=datetime_format, errors='coerce')
        df['ABFAHRTSZEIT'] = pd.to_datetime(df['ABFAHRTSZEIT'], format=datetime_format, errors='coerce')

        return df

    def load_didok(self, path: str, valid_bpuics=None) -> pd.DataFrame:
        df = pd.read_csv(path, sep=";")
        df["number"] = df["number"].astype(int)
        df = df.dropna(subset=["wgs84North", "wgs84East"]).drop_duplicates(subset="number", keep="first")
        if valid_bpuics is not None:
            df = df[df["number"].isin(valid_bpuics)]
        return df


class SparkSBBDataLoader(AbstractSBBDataLoader):
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("SwissRailwayNetwork") \
            .master("spark://spark-master:7077") \
            .getOrCreate()

    def load_istdaten(self, path: str):
        df = self.spark.read.csv(path, sep=";", header=True, inferSchema=True)
        df = df.filter((col("PRODUKT_ID") == "Zug") & (col("FAELLT_AUS_TF") == "false"))
        df = df.withColumn("BPUIC", col("BPUIC").cast(IntegerType()))

        # Specify format explicitly
        timestamp_format = "dd.MM.yyyy HH:mm"
        df = df.withColumn("ANKUNFTSZEIT", to_timestamp("ANKUNFTSZEIT", timestamp_format))
        df = df.withColumn("ABFAHRTSZEIT", to_timestamp("ABFAHRTSZEIT", timestamp_format))

        return df.toPandas()

    def load_didok(self, path: str, valid_bpuics=None):
        df = self.spark.read.csv(path, sep=";", header=True, inferSchema=True)
        df = df.withColumn("number", col("number").cast(IntegerType()))
        df = df.dropna(subset=["wgs84North", "wgs84East"])
        df = df.dropDuplicates(["number"])
        if valid_bpuics is not None:
            df = df.filter(col("number").isin(valid_bpuics.tolist()))
        return df.toPandas()
