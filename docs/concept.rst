Concept
=======

The project aims at discovering problems in the OpenPolitici database.

A Rule contains a description on how to check if the data contains issues.
The Rule is implemented by a programmer and can then be launched (alone, or together with other rules).

A launch produces a Verification, that is related to the Rule, and, if the Verification fails, it creates a CSV report,
containing the list of problematic records, that can be downloaded for inspection by the operator.

The status of the data, with respect to a given Rule at any given time,
can be deduced from the outcome of the last verification before the timestamp.
- unverified (there were no verifications)
- compliant (last verification successful)
- not compliant (last verification not successful)
- error generating (last verification generated an error)

Verifications are management task commands, that can be launched manually,
by having access to the command line, or through the admin interface (custom action).

A verification tracks the operator launching it and the starting timestamp and duration of the process.

A csv report produced by a verification is accessible by all staff members.

Rules can be created or deleted by admin users, and modified by operators.
Verification can be deleted by operators, but modifications and creation should not be allowed.


