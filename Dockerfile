FROM python:3.11-slim

WORKDIR /app

COPY setup.py ./
COPY infn_ophyd_hal/ infn_ophyd_hal/

RUN pip install --no-cache-dir .

COPY tests/ tests/

CMD ["python", "-m", "pytest", "tests/test_sim_devices.py", "-v"]
