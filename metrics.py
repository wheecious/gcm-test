from google.cloud import monitoring_v3

from datetime import datetime, timedelta


client = monitoring_v3.MetricServiceClient()
project_name = "projects/hamster-441615"

end_time = datetime.now()
start_time = end_time - timedelta(hours=12)

filter_successful_requests = (
    'metric.type="loadbalancing.googleapis.com/https/request_count" '
    'AND metric.label."response_code_class" = "200" '
)

filter_total_requests = (
    'metric.type="loadbalancing.googleapis.com/https/request_count"'
)

request_success = monitoring_v3.types.ListTimeSeriesRequest(
    name=project_name,
    filter=filter_successful_requests,
    interval={
        "start_time": {"seconds": int(start_time.timestamp())},
        "end_time": {"seconds": int(end_time.timestamp())},
    },
    aggregation={
        "alignment_period": {"seconds": 60},
        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
    },
    view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
)

request_total = monitoring_v3.types.ListTimeSeriesRequest(
    name=project_name,
    filter=filter_total_requests,
    interval={
        "start_time": {"seconds": int(start_time.timestamp())},
        "end_time": {"seconds": int(end_time.timestamp())},
    },
    aggregation={
        "alignment_period": {"seconds": 60},
        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_RATE,
    },
    view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
)

successful_requests = client.list_time_series(request=request_success)

total_requests = client.list_time_series(request=request_total)

def success_count():
    req = 0
    for request in successful_requests:
        req += 1
    return(req)

def total_count():
    req = 0
    for request in total_requests:
        req += 1
    return(req)


total_req = total_count()

success_req = success_count()

sli = (success_req / total_req) * 100

print(f'total:{total_req}')
print(f'success:{success_req}')

print(f'success percent ratio:{sli}')

#print(f'success:{success_count()}')
#print(f'total:{total_count()}')
