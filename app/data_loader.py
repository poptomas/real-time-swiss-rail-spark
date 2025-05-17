from pyspark.sql import SparkSession
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
        df['ANKUNFTSZEIT'] = pd.to_datetime(df['ANKUNFTSZEIT'], errors='coerce')
        df['ABFAHRTSZEIT'] = pd.to_datetime(df['ABFAHRTSZEIT'], errors='coerce')
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

    def load_istdaten(self, path: str) -> pd.DataFrame:
        df_spark = self.spark.read.option("header", True).option("sep", ";").csv(path)
        df_spark = df_spark.filter((col("PRODUKT_ID") == "Zug") & (col("FAELLT_AUS_TF") == "False"))
        df_spark = df_spark.withColumn("BPUIC", col("BPUIC").cast("int"))
        df_spark = df_spark.withColumn("ANKUNFTSZEIT", to_timestamp(col("ANKUNFTSZEIT"), "dd.MM.yyyy HH:mm"))
        df_spark = df_spark.withColumn("ABFAHRTSZEIT", to_timestamp(col("ABFAHRTSZEIT"), "dd.MM.yyyy HH:mm"))
        return df_spark.toPandas()

    def load_didok(self, path: str, valid_bpuics=None) -> pd.DataFrame:
        df_spark = self.spark.read.option("header", True).option("sep", ";").csv(path)
        df_spark = df_spark.withColumn("number", col("number").cast("int"))
        df_spark = df_spark.filter(col("wgs84North").isNotNull() & col("wgs84East").isNotNull())
        df_pandas = df_spark.toPandas().drop_duplicates(subset="number", keep="first")
        if valid_bpuics is not None:
            df_pandas = df_pandas[df_pandas["number"].isin(valid_bpuics)]
        return df_pandas
