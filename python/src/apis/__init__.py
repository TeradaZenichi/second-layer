from flask_restx import Api
from .setups import api as ns1
from .devices import api as ns2
from .connectors import api as ns3


api = Api(
    title='Microgrid API',
    version='1.0',
    description='API to collect data from microgrid components',
)

api.add_namespace(ns1)
api.add_namespace(ns2)
api.add_namespace(ns3)