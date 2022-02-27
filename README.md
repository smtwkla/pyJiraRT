# pyJiraRT

###A python project to automate creation of recurring tasks in JIRA.

Creation of recurring tasks in JIRA can be automated with this tool. Tasks can be created on specific dates of month on specific months.
* Searches for tasks begining with text "AutoRT " in all projects with status as "Done".
* Parses the task's subject text for formatted instructions & conditions on it.
* Creates tasks on the same project if the conditions are met, as per the instructions
* Logs the processing done to a project ment for logging. Key for the log project is specified in settings.py


##Format:

AutoRT Text_of_Title_to_Create [Date Formating macros] {<date_to_create> | *, <month_tocreate> | *, <create_before_days> | 0 } 

##Date Formatting Macros:
- %M - Month of Due Date
- %Y - Year of Due Date
- %PM - previous month
- %PY - previous year
- %m - current month
- %y - current year
 
##Example: 
* AutoRT Credit Card Pmt 2587 24th %M {24,\*, 4} 
* This will create a task titled "Credit Card Pmt 2587 24th <Month>" on 20th of every month, with due date set to 24th.
* create_before_days - if zero, created on the date & month specified. If greater than zero, for ex: 4, creates the task 4 days before the date & month specified. Due date is also set accordingly.