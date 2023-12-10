'''Custom Exception Class '''

class InvalidInputError(Exception):
    message = "Invalid input"

class EmptyPageError(Exception):
    message = "Generator have no page attached"

class BaseUrlRequiredError(Exception):
    message = 'This method requires a base url'

class PageURLRequiredError(Exception):
    message = 'page url is missing'

class PageNotFoundError(Exception):
    message = 'URL is not a valid endpoint. It returns 404 on request'

class FileAlreadyExists(Exception):
    message = 'The file path you are trying to download already exists'

class AuthenticationError(Exception):
    message = 'You are not authorized to access this page'