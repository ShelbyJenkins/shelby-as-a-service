from app.services.factory import ServiceBase
from app.services.ceq_agent import CEQAgent

dep = ServiceBase()
ce = CEQAgent(ceq_docs_max_used=6)
 