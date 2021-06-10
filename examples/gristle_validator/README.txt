CSV Dialect Examples:
    Example-01: quote_none with escaping of delimiters and newlines
    Example-02: quote_none with skipinitial space
    Example-03: quote_none with auto-detection of delimiter, and header
    Example-04: quote_all with double-quoting to ignore embedded quotes
    Example-05: quote_all with escapechar to ignore embedded quotes
    Example-06: quote_minimum
    Example-07: quote_nonnumeric

Primary Feature Examples:
    Example-21: validate file with inconsistent field count - based on comparing records
                - Demonstrates checking each record for field counts against the count of 
                  fields found on the first record.
    Example-22: validate file with inconsistent field count - based on option value
                - Demonstrates checking for field counts against the  cli option field-cnt.
    Example-23: validate file with valid schema
                - Shows how all records will be written as-is to the output file when each
                  passes all field count and schema checks.
    Example-24: validate file with invalid data and err-out-fields
                - Provides error info in three fields appended to end of records
                  within the errfile.
                - The field are: error-count, and then for the first error encountered:
                  the column_number, the check that was violated, and the error msg.
    Example-24: validate file with invalid data and err-out-text
                - Provides error info on records following any invalid record in the errfile.
                - Each invalid column of the invalid record will get three records written
                  that identify the column, the check that was violated, and the error msg.
                - This method gives the best error info, but the error info is more human
                  readable than machine parsed.
