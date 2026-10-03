# Tablekeeper Stage 2 baseline

Build and run the HTTP service with Docker from a clean checkout. No local Python
installation, Compose file, database, or run-time network access is required.

```powershell
docker build -t tablekeeper:stage-2 .\stage-2
docker run --rm --name tablekeeper-stage-2 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 tablekeeper:stage-2
```

The service listens on `0.0.0.0` inside the container. Check readiness from a
second terminal:

```powershell
Invoke-RestMethod http://localhost:8080/health
```

The response is `{"status":"ok"}`. Container state is in memory and may be lost
when the container stops. The image includes IANA timezone data for restaurant
local times and daylight-saving transitions.
