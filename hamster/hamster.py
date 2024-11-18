from flask import Flask, render_template

from google.cloud import monitoring_v3

from google.api_core.datetime_helpers import to_rfc3339

from datetime import datetime, timedelta

app = Flask(__name__)

client = monitoring_v3.MetricServiceClient()

f = open('../project', 'r')
proj = f.read()
project_name = f'projects/{proj.strip()}'
f.close()

#2xx filter
filter_successful_requests = (
    'metric.type="loadbalancing.googleapis.com/https/request_count" '
    'AND metric.label."response_code_class" = "200" '
)

#>4xx reqs filter
filter_total_requests = (
    'metric.type="loadbalancing.googleapis.com/https/request_count"'
)

#aggregate successful reqs
def request_success():
    reqs = monitoring_v3.types.ListTimeSeriesRequest(
        name=project_name,
        filter=filter_successful_requests,
        interval={
            "start_time": {"seconds": int(start_time.timestamp())},
            "end_time": {"seconds": int(end_time.timestamp())},
        },
        aggregation={
            "alignment_period": {"seconds": 3600},
            "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
        },
        view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
    )
    return reqs
#aggregate all reqs
def request_total():
    reqs = monitoring_v3.types.ListTimeSeriesRequest(
        name=project_name,
        filter=filter_total_requests,
        interval={
            "start_time": {"seconds": int(start_time.timestamp())},
            "end_time": {"seconds": int(end_time.timestamp())},
        },
        aggregation={
            "alignment_period": {"seconds": 3600},
            "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
        },
        view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        )
    return reqs

def count_requests(request):
    reqs = 0
    for entry in request:
        for point in entry.points:
            reqs += point.value.int64_value
    return reqs


#display flask pages
@app.route('/')
def health_check():
    return('200')

@app.route('/ratio')
def show_index():
    #time range
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=12)

    successful_requests = client.list_time_series(request=request_success())
    total_requests = client.list_time_series(request=request_total())
    success = count_requests(successful_requests)
    total = count_requests(total_requests)

    #calculate success vs total ratio
    sli = ( success / total ) * 100

    return render_template('index.html', total=total,
                            success=success, sli=sli)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080) # nosec
