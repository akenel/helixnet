# HelixNETWORK - TELL ME System
# The network layer that connects CRACKs

"""
TELL ME Network Protocol:

1. CRACK broadcasts "I need X" → tell_me.requests
2. Network routes to all connected shops
3. Shops respond "I have X, price Y" → tell_me.responses
4. CRACK selects best offer
5. Order placed → tell_me.orders
6. Fulfillment tracked

Share the JAM.
"""

from .tell_me import TellMeService, TellMeRequest, TellMeResponse, TellMeOrder

__all__ = ['TellMeService', 'TellMeRequest', 'TellMeResponse', 'TellMeOrder']
