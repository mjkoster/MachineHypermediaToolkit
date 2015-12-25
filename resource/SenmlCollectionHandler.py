import terms as v
from HypermediaResource import ContentHandler
from SenmlHandler import Senml

class SenmlCollectionHandler(ContentHandler):
        
    _contentFormat = v.senmlCollectionType
    
    def __postInit__(self):
        self._senml = SenmlCollection(baseName=self._resource._pathString)
        
    def _processRequest(self, request):
        
        if v.get == request[v.method]:
            """ return a representation of a collection+senml instance with links and items
                first process the query and load the list of matching links into the senml 
                object; if the query is empty, all links are returned """
            self._senml.init( self._resource._linkArray.get(request[v.uriQuery]), baseName=self._resource._pathString )
            if [] == self._senml.getLinks() :
                request[v.response][v.status] = v.NotFound
                return
            """ clear the query parameters as they are consumed """
            request[v.uriQuery] = {}
            """ get representations of the items """
            for self._link in self._senml.getLinks():
                if v._rel in self._link and v._item == self._link[v._rel] :
                    """ get item in local context and add to the result """
                    self._senml.addItems( self._resource._itemArray.getItemByName(self._link[v._href]) )
                elif v._rel in self._link and v._sub == self._link[v._rel] :
                    """ get subresource item """
                    request[v.uriPath] = self._resource._uriPath + self._link[v._href]
                    self._subresources[self._link[v._href]].routeRequest(request)
                    """ send request and wait for response """
                    if v.Success == request[v.response][v.status]:
                        self._senml.addItems( Senml.load(request[v.response][v.payload]).items() )
                    else:
                        """ if there is any error, return with the error status in the response """
                        return
            request[v.response][v.payload] = self._senml.serialize()                    
            request[v.response][v.status] = v.Success
            
        elif v.post == request[v.method]:
            """ create new items in the collection. Takes a senml document with or without 
                a links element. If the links element is elided, default links are constructed """
            self._senml.init()
            self._senml.load(request[v.payload])
            for item in self._senml.items():
                if [] == self._senml.getLinks({v._href: item[v._n]}):
                    """make a default item link if no link was provided for this item"""
                    self._senml.addLinks({v._href: item[v._n], v._rel: v._item})
                """add the link to the links array"""
                self._resource._linkArray.add(self._senml.getLinks({v._href: item[v._n]}) )
                if [] != self._senml.getLinks({v._href: item[v._n], v._rel: v._item}):
                    """ make an item """
                    self._resource._itemArray.add(item)
                elif [] != self._senml.getLinks({v._href: item[v._n], v._rel: v._sub}):
                    """ make a subresource """
                    self._resource._createSubresource(item[v._n])
            request[v.response][v.status] = v.Success


from Links import Links
         
class SenmlCollection(Senml):
    
    def __init__(self, links=None, items=None, baseName=None):
        Senml.__init__(self, items, baseName)
        self._links = Links(links)
        self._senml[v._l] = self._links._links
        
    def init(self, items=None, links=None, baseName=None):
        self.__init__(items, links, baseName)
                
    def addLinks(self, links):        
            self._links.add(links)  
            
    def getLinks(self, selectMap=None):
            return self._links.get(selectMap)

    def load(self, jsonString):
        Senml.load(self, jsonString)
        if v._l in self._loadObject :
            self.addLinks(self._loadObject[v._l])

