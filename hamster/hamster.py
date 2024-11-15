from flask import Flask, render_template

from google.cloud import monitoring_v3

from datetime import datetime, timedelta

app = Flask(__name__)

f = open('../project', 'r')

client = monitoring_v3.MetricServiceClient()
project_name = f'projects/{f.read()}'

f.close()

#time range
end_time = datetime.now()
start_time = end_time - timedelta(hours=12)

#2xx 3xx reqs filter
filter_successful_requests = (
    'metric.type="loadbalancing.googleapis.com/https/request_count" '
    'AND metric.label."response_code" >= "200" '
    'AND metric.label."response_code" < "400"'
)

#>4xx reqs filter
filter_total_requests = (
    'metric.type="loadbalancing.googleapis.com/https/request_count"'
)

#aggregate successfull reqs
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
#aggregate all reqs
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

#get reqs data
successful_requests = client.list_time_series(request=request_success)
total_requests = client.list_time_series(request=request_total)

#count received reqs
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

#display flask pages
@app.route('/')
def health_check():
    return('200')

@app.route('/ratio')
def show_index():

    #calculate success vs total ratio
    sli = (success_count() / total_count()) * 100

    return render_template('index.html', total=total_count(),
                            success=success_count(), sli=sli)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080) # nosec
