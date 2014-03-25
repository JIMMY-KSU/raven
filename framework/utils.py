def toString(s):
  if type(s) == type(""):
    return s
  else:
    return s.decode()
    
def toBytes(s):
  if type(s) == type(""):
    return s.encode()
  elif type(s).__name__ in ['unicode','str','bytes']: return bytes(s)
  else:
    return s

def toBytesIterative(s):
  if type(s) == list: return [toBytes(x) for x in s]
  elif type(s) == dict:
    if len(s.keys()) == 0: return None
    tempdict = {}
    for key,value in s.items(): tempdict[toBytes(key)] = toBytesIterative(value)
    return tempdict
  else: return toBytes(s) 

def toStrish(s):
  if type(s) == type(""):
    return s
  elif type(s) == type(b""):
    return s
  else:
    return str(s)

def convertDictToListOfLists(inputDict):
  if type(inputDict) == dict:
    returnList = [[],[]]
    for key, value in inputDict.items():
      returnList[0].append(key)
      if type(value) == dict: returnList[1].append(convertDictToListOfLists(value))
      else: returnList[1].append(value)
  else:   
    print('UTILS         : WARNING -> in method "convertDictToListOfLists", inputDict is not a dictionary!')
    returnList = None
  return returnList


def metaclass_insert(metaclass,*base_classes):
  """This allows a metaclass to be inserted as a base class.
  Metaclasses substitute in as a type(name,bases,namespace) function,
  and can be anywhere in the hierarchy.  This instantiates the 
  metaclass so it can be used as a base class.
  Example use:
  class Foo(metaclass_insert(Metaclass)):
  This function is based on the method used in Benjamin Peterson's six.py
  """
  namespace={}
  return metaclass("NewMiddleMeta",base_classes,namespace)

class abstractstatic(staticmethod):
  """This can be make an abstract static method
  import abc
  class A(metaclass_insert(abc.ABCMeta)):
    @abstractstatic
    def test():
      pass
  class B(A):
    @staticmethod
    def test():
      return 5
  """
  def __init__(self, function):
    super(abstractstatic, self).__init__(function)
    function.__isabstractmethod__ = True
  __isabstractmethod__ = True
