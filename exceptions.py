'''Custom Exception Class '''

class InvalidInputError(Exception):
    message = "Invalid input"

class EmptyPageError(Exception):
    message = "Generator have no page attached"

class BaseUrlRequiredError(Exception):
    message = 'This method requires a base url'

class PageNotFoundError(Exception):
    message = 'URL is not a valid endpoint. It returns 404 on request'