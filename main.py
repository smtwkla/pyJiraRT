import re
import datetime
import calendar
from jira import JIRA
import json
import html
import secrets

def fmt_summary(summary, create_date, due_date):
    month = "%m"
    year = "%y"

    prev_month_due = "%PM"
    prev_year_due = "%PY"

    month_due = "%M"
    year_due = "%Y"

    if summary.find(prev_month_due) != -1:
        summary = summary.replace(prev_month_due, \
                                  calendar.month_name[due_date.month - 1 if due_date.month > 1 else 12][0:3])
    if summary.find(prev_year_due) != -1:
        summary = summary.replace(prev_year_due, str(due_date.year - 1))

    if summary.find(month) != -1:
        summary = summary.replace(month, create_date.strftime("%b"))
    if summary.find(year) != -1:
        summary = summary.replace(year, create_date.strftime("%Y"))

    if summary.find(month_due) != -1:
        summary = summary.replace(month_due, due_date.strftime("%b"))
    if summary.find(year_due) != -1:
        summary = summary.replace(year_due, due_date.strftime("%Y"))

    return summary


def check_if_last_day_of_month(dt):
    dates_month = dt.month
    tomorrows_month = (dt + datetime.timedelta(days=1)).month
    return True if tomorrows_month != dates_month else False


def lambda_handler(event, context):

    url_run_date = url_run_month = url_run_year = url_run_proj = None

    jira = JIRA(server='https://smtw-jira.atlassian.net/', basic_auth=(secrets.USER_NAME, secrets.PASSWORD))

    # run_date = datetime.datetime(2022, 1, 18)
    run_date = datetime.datetime.now()

    try:
        request_data = event['queryStringParameters']
        url_run_date = int(html.escape(request_data['rundate']))
        url_run_month = int(html.escape(request_data['runmonth']))
        url_run_year = int(html.escape(request_data['runyear']))
        if 'runproj' in request_data:
            pattern = re.compile('\W')
            url_run_proj = re.sub(pattern, '', html.escape(request_data['runproj']))

        run_date = datetime.datetime(url_run_year, url_run_month, url_run_date)

    except (TypeError, ValueError, KeyError):
        pass

    log_task = jira.create_issue(project="ARTL", summary=run_date.strftime("%Y-%m-%d"), issuetype={"name": "Task"})

    jql = "summary ~ AutoRT AND status = done" + ((" AND project =" + url_run_proj) if url_run_proj is not None else "")
    rt_issues = jira.search_issues(jql_str=jql)
    ignored = 0
    processed = 0
    created = 0

    for issue in rt_issues:
        iss_summary = issue.fields.summary
        if iss_summary.startswith('AutoRT'):
            open_br = iss_summary.find("{")
            close_br = iss_summary.find("}")
            comma1 = iss_summary.find(",")
            comma2 = iss_summary.find(",", comma1 + 1)
            cur_prj = issue.fields.project.key
            if open_br != -1 and close_br != -1 and close_br > open_br and \
                    comma1 != -1 and close_br > comma1 > open_br and comma2 < close_br:
                iss_arg1 = iss_summary[open_br + 1:comma1]
                iss_arg2 = iss_summary[comma1 + 1:comma2]
                iss_arg3 = iss_summary[comma2 + 1:close_br]

                date_to_create = month_to_create = date_all = month_all = date_last = False
                due_date = None

                try:
                    date_to_create = int(iss_arg1)
                except ValueError:
                    if iss_arg1 == "*":
                        date_all = True
                    elif iss_arg1 == "L":
                        date_last = True
                try:
                    month_to_create = int(iss_arg2)
                except ValueError:
                    if iss_arg2 == "*":
                        month_all = True
                try:
                    due_in = int(iss_arg3)
                except ValueError:
                    due_in = 0

                chk_date = run_date + datetime.timedelta(days=due_in)

                if date_last:
                    date_to_create = calendar.monthrange(run_date.year, run_date.month)[1]

                if month_all or month_to_create == chk_date.month:
                    if date_all or date_to_create == chk_date.day:
                        due_date = chk_date

                        new_summary = fmt_summary(iss_summary[7:open_br], run_date, due_date)
                        print(issue.key, cur_prj, iss_arg1, iss_arg2, iss_arg3, new_summary)
                        created_issue = jira.create_issue(project=cur_prj, summary=new_summary, \
                                                          duedate=due_date.strftime("%Y-%m-%d") if due_in > 0 else None, \
                                                          issuetype={"name": "Task"})
                        created += 1
                    else:
                        processed += 1
            else:
                ignored += 1
        else:
            ignored += 1

    log_msg = 'Issues ignored: %d; Processed: %d; Created: %d' % (ignored, processed, created)
    log_task.update(notify=False, \
                    fields={'description': log_msg})
    jira.transition_issue(log_task, transition="Done")
    jira.close()

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda! ' + log_msg)
    }


if __name__ == "__main__":
    lambda_handler(None, None)
