from simple_salesforce import Salesforce
import collections
import argparse
import keyring
import sys
import os
import textwrap
import signal

# To suppress the BrokenPipeError message that gets raised when a pipe is used for stdout
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

URL='https://mongodb.my.salesforce.com'
TOKEN_SECRET_NAME = 'SF_TOKEN'
TOKEN = keyring.get_password("system", TOKEN_SECRET_NAME)
USERNAME = 'user@mongodb.com'
PASSWORD = keyring.get_password("system", USERNAME)
# PROCESS_KV = True

TERMINAL_SIZE = int()
if sys.stdout.isatty():
    TERMINAL_SIZE = os.get_terminal_size().columns
else:
    TERMINAL_SIZE = 128

## TODO: Find a way to list the attachments

class Order():
    ASC = "ASC"
    DESC = "DESC"

def ASC():
    return Order.ASC

def DESC():
    return Order.DESC

def orderSelector(input):
    switcher = {
        "asc": ASC,
        "desc": DESC
    }
    func = switcher.get(input, lambda: "Invalid")
    return func()

class Query:
    PredicateFields = list()
    Table = str()
    Limit = int()
    Sort = object()

    def __init__(self, predicatesList, table, SaleForceInstance):
        self.Table = table
        self.PredicateFields = predicatesList
        self.SF = SaleForceInstance
        self.Conditions = list()
        self.Sort = QuerySort("", [])

    def addCondition(self, conditionType, conditionColumn, conditionValue):
        self.Conditions.append(QueryCondition(conditionType, conditionColumn, conditionValue))
    
    def setLimit(self, limit):
        self.Limit = limit
    
    def setSort(self, order, fieldsList):
        self.Sort.Order = order
        self.Sort.Fields = fieldsList

    def asText(self):
        queryText = "SELECT "
        i = 0
        for f in self.PredicateFields:
            queryText = queryText + f
            if i < len(self.PredicateFields) - 1:
                queryText = queryText + ", "
            i = i + 1
        queryText = queryText + " FROM " + self.Table
        if len(self.Conditions) > 0:
            queryText = queryText + " WHERE "
            i = 0
            for c in self.Conditions:
                if i > 0:
                    queryText = queryText + " AND "
                queryText = queryText + c.asText()
                i = i + 1
        
        if len(self.Sort.Fields) > 0:
            queryText = queryText + " " + self.Sort.asText()
        if self.Limit > 0:
            queryText = queryText + " LIMIT " + str(self.Limit)

        return queryText        

    def run(self):
        return runSOQL(self.asText(), self.SF)

class QueryCondition:
    Type = str()
    Column = str()
    Value = str()

    def __init__(self, type, column, value):
        self.Type = type
        self.Column = column
        self.Value = value

    def asText(self):
        return self.Column + " " + self.Type + " '" + self.Value + "' "

class QueryConditionType:
    eq = "="
    gt = ">"
    gte = ">="
    lt = "<"
    lte = "<="

class QuerySort:
    Order = str()
    Fields = list()

    def __init__(self, order, fields):
        self.Fields = fields
        self.Order = order
    
    def asText(self):
        text = " "
        if len(self.Fields) > 0:
            text = text + "ORDER BY"
            i = 0
            for f in self.Fields:
                if i > 0:
                    text = text + ","
                text = text + " " + f
                i = i + 1
            text = text + " " + self.Order
        return text

class Case:
    Number = str()
    Id = str()
    Status = str()
    Priority = str()
    Owner = str()
    Subject = str()
    attributes = dict()
    Comments = list()
    Description = str()
    NumCommentsToShow = int()

    def __init__(self, sfInstance, number, commentsToShow, commentsOrder):
        self.Number = number
        self.SF = sfInstance
        self.NumCommentsToShow = commentsToShow
        self.fetchCaseDetails()
        self.fetchComments(commentsOrder, True)

    def print(self, printComments=False):
        try:
            printSeparator(self.Number)
            print("+")
            print("└--+ attributes : ")
            print("|  └--- type :  " + self.attributes['type'])
            print("|  └--- url :  "+ self.attributes['url'])
            print("└- Status : " + self.Status)
            print("└- Priority : " + self.Priority)
            print("└- Owner : " + self.Owner)
            print("└- Subject : " + self.Subject)
            print("└- Comments : " + str(len(self.Comments)))
            print("└- Description : ")

            printSeparator(symbol="_")
            print(indent(self.Description))
            printSeparator(symbol="_")
            if printComments is True:
                i = 0
                for c in self.Comments:
                    if i == self.NumCommentsToShow:
                        break
                    c.print()
                    i = i + 1
            printSeparator(self.Number)
        except BrokenPipeError:
            sys.exit()

    def setOwner(self, Owner):
        for word in Owner.split(" "):
            if word == "[<a":
                break
            if(len(self.Owner) > 0):
                self.Owner = self.Owner + " " + word
            else:
                self.Owner = self.Owner + word

    def fetchCaseDetails(self):
        # Get the ticket Id
        CaseQueryColumns = [ 
            'Case_ID_18__c',
            'CaseNumber',
            'Status',
            'Priority',
            'Owner__c',
            'Subject',
            'Description'
        ]
        CaseQuery = Query(CaseQueryColumns, "Case", self.SF)
        CaseQuery.addCondition(QueryConditionType.eq, "CaseNumber", self.Number)
        CaseQuery.setLimit(1)
        res = CaseQuery.run()
        # TODO: Catch an exception here
        if res is not None:
            # TODO: Change this if-else logic
            if len(res['records']) > 0:
                r = res['records'][0]
                self.attributes = r['attributes']
                self.Id = r['Case_ID_18__c'] 
                self.Status = r['Status']
                self.Priority = r['Priority']
                self.setOwner(r['Owner__c'])
                self.Subject = r['Subject']
                self.Description = r['Description']
            else:
                print("The query yielded 0 records") 
        else:
            print("ERROR: SalesForce query was unsuccessful")

    def fetchComments(self, order, fetchAll=False):
        CommentsQuery = Query(["Id"], "Case_Comment__c", self.SF)
        CommentsQuery.addCondition(QueryConditionType.eq, "Case__c", self.Id)
        CommentsQuery.setSort(order, ["Created_DateTime__c"])
        # Get the list of comments Ids
        res = CommentsQuery.run()
        # TODO: Catch an exception here
        if res is not None:
            # TODO: Change this if-else logic
            if len(res['records']) > 0:
                for rec in res['records']:
                    comment = CaseComment(rec['attributes']['type'], rec['attributes']['url'], rec['Id'], self.Id, self.SF)
                    # TODO: It should be more efficient to query the comment text in the same query
                    if fetchAll is True:
                        comment.fetch(self.SF)
                    self.Comments.append(comment)
            else:
                print("The query yielded 0 records")
        else:
            print("ERROR: SalesForce query was unsuccessful")

class CaseComment:
    CaseId = str()
    attributes = dict()
    Id = str()
    Created_By = str()
    Created = str()
    IsDeleted = bool()
    IsPublished = bool()
    Markdown_Text = str()
    Name = str()

    def __init__(self, type, url, Id, CaseId, sfInstance):
        self.attributes['type'] = type
        self.attributes['url'] = url
        self.Id = Id
        self.CaseId = CaseId
        self.fetch(sfInstance)

    def print(self):
        try:
            printSeparator(self.Name)
            print("+")
            print("└--+ attributes : ")
            print("|  └--- type :  " + self.attributes['type'])
            print("|  └--- url :  "+ self.attributes['url'])
            print("└- CaseId : " + self.CaseId)
            print("└- Id : " + self.Id)
            print("└- Name : " + self.Name)
            print("└- Created_By : " + self.Created_By)
            print("└- Created : " + self.Created)
            print("└- IsDeleted : " + str(self.IsDeleted))
            print("└- IsPublished : " + str(self.IsPublished))
            print("└- Markdown_Text : ")
            printSeparator(symbol="-")
            print(indent(self.Markdown_Text))
            printSeparator(symbol="-")
            printSeparator(self.Name)
        except BrokenPipeError:
            sys.exit()
    
    def fetch(self, sfInstance):
        # Get the comment by Id
        CommentQueryColumns = [
            "Name",
            "Created_By_Name__c",
            "Created_DateTime__c",
            "IsDeleted",
            "Is_Published__c",
            "Markdown_Text__c",
        ] 
        CommentQuery = Query(CommentQueryColumns, "Case_Comment__c", sfInstance)
        CommentQuery.addCondition(QueryConditionType.eq, "Case__c", self.CaseId)
        CommentQuery.addCondition(QueryConditionType.eq, "Id", self.Id)
        CommentQuery.setLimit(1)
        res = CommentQuery.run()
        if res is not None:
            # TODO: Change this if-else logic
            if len(res['records']) > 0:
                r = res['records'][0]
                # Let's update the attributes anyway
                self.attributes = r['attributes']
                self.Created_By = r['Created_By_Name__c']
                self.Created = r['Created_DateTime__c']
                self.IsDeleted = r['IsDeleted']
                self.IsPublished = r['Is_Published__c']
                self.Markdown_Text = r['Markdown_Text__c']
                self.Name = r['Name']
            else:
                print("The query yielded 0 records") 
        else:
            print("ERROR: SalesForce query was unsuccessful")

# Some helpers

def indent(text):
    if len(text) > 0:
        text = textwrap.indent(text=text, prefix='    ')
    return text

def printSeparator(label="",symbol="="):
    width = TERMINAL_SIZE
    if len(label) == 0:
        line = "\n"
        for pos in range(width):
            line = line + symbol
    else:
        sectionLen = int((width - len(label) - 2)/2)
        line = "\n"
        for pos in range(sectionLen):
            line = line + symbol
        line = line + " " + label + " "
        for pos in range(sectionLen):
            line = line + symbol
    line = line + "\n"
    print(line)


# Check if the ticket number is matching the expected pattern
def sanitizeTicketArgument(tkArg):
    good = True
    if (len(tkArg) != 8):
        good = False
    for c in tkArg:
        if (c.isalpha()):
            good = False

    return good


# To process the command line arguments
def processArguments():
    parser = argparse.ArgumentParser(description='Query tickets information from SalesForce')
    parser.add_argument('ticket', metavar='T', type=str, nargs=1, help='8-digit ticket number')
    parser.add_argument('--order', metavar='O', type=str, nargs=1, help='order of comments to display; accepted values: asc, desc', default=['asc'])
    parser.add_argument('--num', metavar='N', type=int, nargs=1, help='number of comments to display at once', default=-1)
    args = parser.parse_args()

    ticket = ""
    order = ""
    num = None

    for t in args.ticket:
        if sanitizeTicketArgument(t) == False:
            print("ERROR: The specified argument does not appear to be a ticket number: %s \n" % t)
            parser.print_help()
            sys.exit()

        if (len(ticket) == 0):
            ticket = t 

    if "order" in args:
        order = order + orderSelector(args.order[0])

        if order == "Invalid":
            print("ERROR: the order should either be asc or desc")
            parser.print_help()
            sys.exit()
            
    if "num" in args:
        num = args.num[0]
    
    return ticket, order, num

def runSOQL(query, sfInstance):
    try:
        result = sfInstance.query(query)
    except:
        print("FATAL ERROR: SalesForce could not be run: ", sys.exc_info()[0])
        raise
        sys.exit()

    if result['done'] != True:
        result = None

    return result

def main():
    
    ticket,order,num = processArguments()

    try:
        sf = Salesforce(instance_url=URL, username=USERNAME, password=PASSWORD, security_token=TOKEN)
    except:
        print("FATAL ERROR: SalesForce could not be accessed with the provided credentials")
        raise
        sys.exit()

    case = Case(sf, ticket, num, order)
    case.print(True)
     
if __name__ == '__main__':
    main()
