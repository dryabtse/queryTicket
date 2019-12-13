# queryTicket
A script that retrieves a support ticket data from SalesForce

### Requirements
- Python 3
- You will need to generate an API token for your account in SalesForce
- The script expects the token and the user password to be stored and retrieved using [keyring](https://pypi.org/project/keyring/) (supports Keychain as a backend on OSX)

```
$ python3 queryTicket.py 
usage: queryTicket.py [-h] [--order O] [--num N] T
queryTicket.py: error: the following arguments are required: T
```

This will return only the ticket's details including the description, no comments will be printed:
```
python3 queryTicket.py 00623128 --num 0
```
This will return the case's details along with the latest comment on the ticket:
```
python3 queryTicket.py 00623128 --num 1 --order desc
```

This will return the case's details along with the first comment
```
python3 queryTicket.py 00623128 --num 1 
```
