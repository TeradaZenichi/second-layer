from flask_restx import Api
from .setups import api as ns1
from .evcs import api as ns2
from .bess import api as ns3
from .pv import api as ns4
from .config import api as ns5



api = Api(
    title='DERs Second Layer API',
    version='1.0',
    description='API to manage DERs and their connections to the grid.',
)

api.add_namespace(ns1, path='/ders/secondlayer/setups')
api.add_namespace(ns2, path='/ders/secondlayer/evcs')
api.add_namespace(ns3, path='/ders/secondlayer/bess')
api.add_namespace(ns4, path='/ders/secondlayer/pv')
api.add_namespace(ns5, path='/ders/secondlayer/timeconfig')