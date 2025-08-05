"""
module for enums for document type
"""

from enum import Enum

"""
Dev Note:

As I get it, there will be 4 types of documents that can be uploaded:

USER_DOCUMENT - used for user verification of persona
(like passport, trading permission etc). It is mainly for complience reasons.


COMPANY_DOCUMENT - used for verification of company's legitimacy. For background
checks, and for legal issues if any are to arrise.

INSTRUMENT_RAW_DOCUMENT - documents based on which the instruments
will be based. This type of documents is the one that we need to make
sure are as obscured from access as possible.

INSTRUMENT_PROCESSED_DOCUMENT - documents which support or fully
represent a given instrument. These are the documents that will be used to make
investment decisions, potentially alongside with some instrument metadata.
"""


class DocumentType(str, Enum):
    USER_DOCUMENT = 'USER_DOCUMENT'
    COMPANY_DOCUMENT = 'COMAPNY_DOCUMENT'
    INSTRUMENT_RAW_DOCUMENT = 'INSTRUMENT_RAW_DOCUMENT'
    INSTRUMENT_PROCESSED_DOCUMENT = 'INSTRUMENT_PROCESSED_DOCUMENT'
