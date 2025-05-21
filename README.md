# Real-Time Visualization and Analysis of Swiss Train Traffic Using Apache Spark

---

## Overview

This project presents a real-time, interactive visualization of the Swiss railway network using publicly available transport data and Apache Spark. Built as a dockerized web application, it allows users to view live traffic patterns and station departure boards across Switzerland.

Our motivation stems from the unique efficiency and significance of the Swiss railway system. With its compact scale and impressive reliability, it presents an ideal opportunity for data-driven visualization and analysis.

---

## Data Sources

We utilize the following datasets:

1. **Zones and Stop Places**  
   Provided by the Swiss Federal Office of Transport (FOT), this dataset includes public transport-relevant areas and stop edges.  
   📎 https://data.opentransportdata.swiss/en/dataset/traffic-points-actual-date

2. **Swiss Public Transport API**  
   A REST API by search.ch offering real-time timetables across different transport modes.  
   📎 https://transport.opendata.ch/

3. **DiDok Service Points**  
   Official dataset maintained by SBB providing detailed geolocation for each station via BPUIC codes.  
   📎 https://data.sbb.ch/explore/dataset/dienststellen-gemass-opentransportdataswiss

---

## Implementation

The project consists of a Spark-powered backend and a Streamlit-based frontend:

- **Real-time data ingestion** from public APIs
- **Graph creation** using NetworkX (stations as nodes, connections as edges)
- **Heatmap visualization** showing usage frequency from green (low) to red (high)
- **Live stationboard** data, refreshed every minute using `streamlit_autorefresh`
- **Interactive map** with hover and click capabilities using Folium

---

## Running the Application

This project is containerized using Docker.

### Requirements

- Docker
- Docker Compose

### 🛠 Setup & Launch

```bash
docker-compose up --build
```

Visit the app at: [http://localhost:8501](http://localhost:8501)

---

## Features

- Real-time visualization of active Swiss train routes  
- Clickable stations showing live departures  
- Map auto-refreshes every 60 seconds  
- Hovering edges displays usage frequency  
- Heatmap encoding for visualizing traffic intensity  

---

## Results

### Heatmap

- Most used connection: **359 rides/day**  
- Highest traffic in and around Zurich (e.g., Zürich HB → Zürich Hardbrücke)  
- Even remote routes are used at least once daily, validating infrastructure efficiency  

### Stationboard

- Real-time updates reflect actual (not planned) departures  
- Updates every minute using Transport Open Data API  
- Robustness maintained despite API rate limits (max 1000 calls/day)  

---

## Tech Stack

- **Apache Spark** – Real-time scalable processing  
- **Docker** – Environment setup and orchestration  
- **Streamlit** – Web application interface  
- **NetworkX** – Graph creation & edge weighting  
- **Folium** – Map and geo-visualization  
- **Pandas** – Data manipulation during initial steps  
- **Python** – Core programming language  

---

## Insights

- Swiss train infrastructure shows high utilization even in low-density regions  
- Real-time data processing provides clear visibility into usage patterns  
- Public APIs are reliable and refresh in near real-time  

---

## Notes

- Application designed for local use only — no cloud resources required  
- API rate limits require responsible refreshing (max 1 request per minute)  
- Performance tuning was done to keep Folium responsive even on large datasets  

---

## Summary

This project successfully combines real-time public data, scalable data processing, and intuitive visualization. It offers a clear picture of Swiss train traffic while showcasing the use of modern data engineering tools like Apache Spark, Docker, and Streamlit.

