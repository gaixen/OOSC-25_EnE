import asyncio
import os
import time
from typing import Dict, Any, List
from datetime import datetime

from .event_bus import EventBus, Event, ProvenanceEnvelope, STREAMS, event_bus
from .voice import AssemblyAIRealtimeTranscriber
from .entityExtractor import InfoExtractionAgent
from .companyProfileAgent import CompanyProfileAgent
from .companyNews import CompanyNewsAgent
from .marketCompetitor import CompetitorMarketAIAgent
from .personEnrichment import PersonEnrichmentAgent
from .suggestion_agent import SuggestionGeneratorAgent
from .ranking_agent import RankingAgent

import logging
logger = logging.getLogger(__name__)

# --- Agent Status Tracking ---
class AgentStatus:
    IDLE = "idle"
    WORKING = "working" 
    COMPLETED = "completed"
    ERROR = "error"

class EnhancedOrchestrator:
    """Enhanced orchestrator with parallel agent execution and event-driven architecture"""
    
    def __init__(self):
        # Initialize agents
        self.entity_extractor = InfoExtractionAgent()
        self.company_profile_agent = CompanyProfileAgent()
        self.company_news_agent = CompanyNewsAgent()
        self.competitor_agent = CompetitorMarketAIAgent()
        self.person_enrichment = PersonEnrichmentAgent()
        self.suggestion_agent = SuggestionGeneratorAgent(os.getenv("GEMINI_API_KEY", "demo-key"))
        self.ranking_agent = RankingAgent()
        
        # Agent status tracking
        self.agent_statuses: Dict[str, str] = {
            'entity_extractor': AgentStatus.IDLE,
            'company_profile': AgentStatus.IDLE,
            'company_news': AgentStatus.IDLE,
            'market_competitor': AgentStatus.IDLE,
            'person_enrichment': AgentStatus.IDLE,
            'suggestion_generator': AgentStatus.IDLE,
            'ranking_agent': AgentStatus.IDLE
        }
        
        # Session state tracking
        self.session_contexts: Dict[str, Dict[str, Any]] = {}
        
    async def start(self):
        """Start the orchestrator and subscribe to events"""
        print("🚀 ORCHESTRATOR: Starting enhanced orchestrator...")
        await event_bus.connect()
        event_bus.start_listening()
        
        print("🔊 ORCHESTRATOR: Subscribing to transcript events...")
        # Subscribe to transcript events
        asyncio.create_task(event_bus.subscribe(
            STREAMS['transcripts'], 
            'orchestrator_group', 
            'orchestrator_main',
            self._handle_transcript_event
        ))
        
        print("🔊 ORCHESTRATOR: Subscribing to domain response events...")
        # Subscribe to domain response events for aggregation
        asyncio.create_task(event_bus.subscribe(
            STREAMS['domain_responses'],
            'orchestrator_group',
            'orchestrator_aggregator', 
            self._handle_domain_response_event
        ))
        
        print("✅ ORCHESTRATOR: Enhanced Orchestrator started and listening for events")
        logger.info("🚀 Enhanced Orchestrator started")
    
    async def _handle_transcript_event(self, event: Event):
        """Handle new transcript events"""
        logger.info(f"📝 Processing transcript event for session: {event.session_id}")
        
        session_id = event.session_id
        text = event.data.get('text', '')
        print(f"🎯 ORCHESTRATOR: Processing transcript: '{text}' for session: {session_id}")
        
        # Update agent status
        await self._update_agent_status('entity_extractor', AgentStatus.WORKING, session_id)
        
        # Process entities
        start_time = time.time()
        print(f"🔍 ORCHESTRATOR: Running entity extraction on: '{text}'")
        entities_result = self.entity_extractor.process_text(text)
        processing_time = time.time() - start_time
        
        print(f"📊 ORCHESTRATOR: Entity extraction completed in {processing_time:.2f}s")
        print(f"📊 ORCHESTRATOR: Extracted entities: {entities_result}")
        
        # Create provenance envelope
        provenance = ProvenanceEnvelope(
            agent_id='entity_extractor',
            timestamp=datetime.now().timestamp(),
            inputs={'text': text},
            outputs=entities_result,
            confidence=0.85,  # Static for now
            sources=['spacy_nlp', 'gemini_llm'],
            processing_time=processing_time
        )
        
        # Update session context
        if session_id not in self.session_contexts:
            self.session_contexts[session_id] = {
                'entities': [],
                'domain_data': {},
                'suggestions': [],
                'provenance_chain': [],
                'transcript_history': []
            }
        
        # Add transcript to history
        self.session_contexts[session_id]['transcript_history'].append({'text': text})
        self.session_contexts[session_id]['entities'] = entities_result.get('extracted_entities', [])
        self.session_contexts[session_id]['provenance_chain'].append(provenance)
        
        # Mark entity extractor as completed
        await self._update_agent_status('entity_extractor', AgentStatus.COMPLETED, session_id, entities_result)
        
        # Trigger parallel domain intelligence agents
        print(f"🚀 ORCHESTRATOR: Triggering domain intelligence for entities: {entities_result.get('extracted_entities', [])}")
        await self._trigger_domain_intelligence(session_id, entities_result)
        
        # Publish entities event
        await event_bus.publish(STREAMS['entities'], Event(
            type='entities_extracted',
            session_id=session_id,
            agent_id='entity_extractor',
            data={
                'entities': entities_result.get('extracted_entities', []),
                'provenance': provenance.to_dict()
            }
        ))
    
    async def _trigger_domain_intelligence(self, session_id: str, entities_result: Dict[str, Any]):
        """Trigger parallel execution of domain intelligence agents"""
        entities = entities_result.get('extracted_entities', [])
        print(f"🔄 ORCHESTRATOR: Triggering domain intelligence with {len(entities)} entities")
        
        # Separate entities by type
        companies = [e for e in entities if e.get('type') == 'ORG']
        persons = [e for e in entities if e.get('type') == 'PERSON']
        
        print(f"🏢 ORCHESTRATOR: Found {len(companies)} companies: {[c.get('name') for c in companies]}")
        print(f"👤 ORCHESTRATOR: Found {len(persons)} persons: {[p.get('name') for p in persons]}")
        
        # Create parallel tasks
        tasks = []
        
        for company in companies:
            company_name = company.get('name', '')
            print(f"🏢 ORCHESTRATOR: Creating tasks for company: '{company_name}'")
            
            # Company Profile Agent
            tasks.append(self._run_company_profile_agent(session_id, company_name))
            
            # Company News Agent  
            tasks.append(self._run_company_news_agent(session_id, company_name))
            
            # Market Competitor Agent
            tasks.append(self._run_market_competitor_agent(session_id, company_name))
        
        for person in persons:
            person_name = person.get('name', '')
            print(f"👤 ORCHESTRATOR: Creating task for person: '{person_name}'")
            # Person Enrichment Agent
            tasks.append(self._run_person_enrichment_agent(session_id, person_name))
        
        # Execute all domain intelligence agents in parallel
        if tasks:
            print(f"🔄 ORCHESTRATOR: Running {len(tasks)} domain intelligence agents in parallel")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            print(f"✅ ORCHESTRATOR: Domain intelligence tasks completed: {len(results)} results")
        else:
            print(f"⚠️ ORCHESTRATOR: No entities found to process, skipping domain intelligence")
            # Still try to generate suggestions with whatever context we have
            await self._check_suggestion_readiness(session_id)
    
    async def _run_company_profile_agent(self, session_id: str, company_name: str):
        """Run company profile agent"""
        await self._update_agent_status('company_profile', AgentStatus.WORKING, session_id)
        
        try:
            # Convert company name to domain format for the profile agent
            domain_name = company_name.lower()
            if not "." in domain_name:
                domain_name = f"{domain_name}.com"
            
            print(f"🏢 ORCHESTRATOR: Converting '{company_name}' to domain '{domain_name}' for profile lookup")
            
            start_time = time.time()
            result = await asyncio.to_thread(self.company_profile_agent.fetch_profile, session_id, domain_name)
            processing_time = time.time() - start_time
            
            print(f"✅ ORCHESTRATOR: Company profile agent succeeded for {domain_name}")
            print(f"✅ ORCHESTRATOR: Got {len(result.get('sources', []))} sources: {result.get('sources', [])}")
            
            provenance = ProvenanceEnvelope(
                agent_id='company_profile',
                timestamp=datetime.now().timestamp(),
                inputs={'company_name': company_name, 'domain_used': domain_name},
                outputs=result,
                confidence=0.8,
                sources=['hunter_io', 'wikipedia'],
                processing_time=processing_time
            )
            
            await self._store_domain_data(session_id, 'company_profile', company_name, result, provenance)
            await self._update_agent_status('company_profile', AgentStatus.COMPLETED, session_id, result)
            
        except Exception as e:
            print(f"❌ ORCHESTRATOR: Company profile agent failed: {e}")
            print(f"❌ ORCHESTRATOR: Exception type: {type(e)}")
            print(f"❌ ORCHESTRATOR: Company name was: '{company_name}', Domain used: '{domain_name if 'domain_name' in locals() else 'N/A'}'")
            logger.error(f"❌ Company profile agent failed: {e}")
            await self._update_agent_status('company_profile', AgentStatus.ERROR, session_id)
    
    async def _run_company_news_agent(self, session_id: str, company_name: str):
        """Run company news agent"""
        await self._update_agent_status('company_news', AgentStatus.WORKING, session_id)
        
        try:
            start_time = time.time()
            result = await asyncio.to_thread(self.company_news_agent.fetch_news, session_id, company_name)
            processing_time = time.time() - start_time
            
            provenance = ProvenanceEnvelope(
                agent_id='company_news',
                timestamp=datetime.now().timestamp(),
                inputs={'company_name': company_name},
                outputs=result,
                confidence=0.75,
                sources=['news_api', 'rss_feeds'],
                processing_time=processing_time
            )
            
            await self._store_domain_data(session_id, 'company_news', company_name, result, provenance)
            await self._update_agent_status('company_news', AgentStatus.COMPLETED, session_id, result)
            
        except Exception as e:
            logger.error(f"❌ Company news agent failed: {e}")
            await self._update_agent_status('company_news', AgentStatus.ERROR, session_id)
    
    async def _run_market_competitor_agent(self, session_id: str, company_name: str):
        """Run market competitor agent"""
        await self._update_agent_status('market_competitor', AgentStatus.WORKING, session_id)
        
        try:
            start_time = time.time()
            result = await asyncio.to_thread(self.competitor_agent.fetch_competitors, session_id, company_name)
            processing_time = time.time() - start_time
            
            provenance = ProvenanceEnvelope(
                agent_id='market_competitor',
                timestamp=datetime.now().timestamp(),
                inputs={'company_name': company_name},
                outputs=result,
                confidence=0.7,
                sources=['market_research', 'competitor_apis'],
                processing_time=processing_time
            )
            
            await self._store_domain_data(session_id, 'market_competitor', company_name, result, provenance)
            await self._update_agent_status('market_competitor', AgentStatus.COMPLETED, session_id, result)
            
        except Exception as e:
            logger.error(f"❌ Market competitor agent failed: {e}")
            await self._update_agent_status('market_competitor', AgentStatus.ERROR, session_id)
    
    async def _run_person_enrichment_agent(self, session_id: str, person_name: str):
        """Run person enrichment agent"""
        await self._update_agent_status('person_enrichment', AgentStatus.WORKING, session_id)
        
        try:
            start_time = time.time()
            result = await asyncio.to_thread(self.person_enrichment.fetch_person_profile, session_id, person_name)
            processing_time = time.time() - start_time
            
            provenance = ProvenanceEnvelope(
                agent_id='person_enrichment',
                timestamp=datetime.now().timestamp(),
                inputs={'person_name': person_name},
                outputs=result,
                confidence=0.8,
                sources=['linkedin_api', 'public_records'],
                processing_time=processing_time
            )
            
            await self._store_domain_data(session_id, 'person_enrichment', person_name, result, provenance)
            await self._update_agent_status('person_enrichment', AgentStatus.COMPLETED, session_id, result)
            
        except Exception as e:
            logger.error(f"❌ Person enrichment agent failed: {e}")
            await self._update_agent_status('person_enrichment', AgentStatus.ERROR, session_id)
    
    async def _store_domain_data(self, session_id: str, agent_type: str, entity_name: str, result: Dict, provenance: ProvenanceEnvelope):
        """Store domain data and check if ready for suggestion generation"""
        if session_id not in self.session_contexts:
            return
            
        # Store the data
        if entity_name not in self.session_contexts[session_id]['domain_data']:
            self.session_contexts[session_id]['domain_data'][entity_name] = {}
        
        self.session_contexts[session_id]['domain_data'][entity_name][agent_type] = result
        self.session_contexts[session_id]['provenance_chain'].append(provenance)
        
        # Publish domain response event
        await event_bus.publish(STREAMS['domain_responses'], Event(
            type='domain_data_ready',
            session_id=session_id,
            agent_id=agent_type,
            data={
                'entity_name': entity_name,
                'agent_type': agent_type,
                'result': result,
                'provenance': provenance.to_dict()
            }
        ))
        
        # Check if we have enough data to generate suggestions
        await self._check_suggestion_readiness(session_id)
    
    async def _handle_domain_response_event(self, event: Event):
        """Handle domain response events for aggregation"""
        # This is where we can implement more sophisticated aggregation logic
        logger.debug(f"📊 Domain data received from {event.agent_id} for session {event.session_id}")
    
    async def _check_suggestion_readiness(self, session_id: str):
        """Check if we have enough domain data to generate suggestions"""
        if session_id not in self.session_contexts:
            return
            
        context = self.session_contexts[session_id]
        entities = context.get('entities', [])
        domain_data = context.get('domain_data', {})
        
        # Simple heuristic: if we have domain data for any entity, generate suggestions
        if domain_data and any(domain_data.values()):
            await self._generate_suggestions(session_id)
    
    async def _generate_suggestions(self, session_id: str):
        """Generate and rank suggestions based on accumulated context"""
        await self._update_agent_status('suggestion_generator', AgentStatus.WORKING, session_id)
        
        try:
            context = self.session_contexts[session_id]
            
            # Prepare input for suggestion generator - flatten domain data for easier access
            raw_domain_data = context.get('domain_data', {})
            domain_info = {}
            
            # Flatten the nested structure for easier access by suggestion agent
            for entity_name, agent_results in raw_domain_data.items():
                for agent_type, result in agent_results.items():
                    if agent_type not in domain_info:
                        domain_info[agent_type] = {}
                    domain_info[agent_type][entity_name] = result
            
            # Also include a direct reference to the raw structure
            domain_info['raw_data'] = raw_domain_data
            
            print(f"🤖 ORCHESTRATOR: Starting suggestion generation with domain_info keys: {list(domain_info.keys()) if isinstance(domain_info, dict) else 'Not a dict'}")
            utterances = [item.get('text', '') for item in context.get('transcript_history', [])]
            print(f"🤖 ORCHESTRATOR: Processing {len(utterances)} utterances")
            
            start_time = time.time()
            suggestion_envelope = await asyncio.to_thread(
                self.suggestion_agent.generate_suggestions, 
                domain_info,
                utterances
            )
            processing_time = time.time() - start_time
            
            print(f"🤖 ORCHESTRATOR: Suggestion generation completed in {processing_time:.2f}s")
            
            # Extract suggestions from envelope
            suggestions = suggestion_envelope.get('outputs', {}).get('suggestions', [])
            print(f"🤖 ORCHESTRATOR: Generated {len(suggestions)} suggestions")
            
            provenance = ProvenanceEnvelope(
                agent_id='suggestion_generator',
                timestamp=datetime.now().timestamp(),
                inputs={'domain_info': domain_info, 'utterances': utterances},
                outputs=suggestion_envelope.get('outputs', {}),
                confidence=suggestion_envelope.get('confidence', 0.8),
                sources=suggestion_envelope.get('sources', ['gemini_llm']),
                processing_time=processing_time
            )
            
            context['suggestions'] = suggestions
            context['provenance_chain'].append(provenance)
            
            await self._update_agent_status('suggestion_generator', AgentStatus.COMPLETED, session_id)
            
            # Now rank the suggestions
            await self._rank_suggestions(session_id, suggestions, provenance)
            
        except Exception as e:
            logger.error(f"❌ Suggestion generation failed: {e}")
            await self._update_agent_status('suggestion_generator', AgentStatus.ERROR, session_id)
    
    async def _rank_suggestions(self, session_id: str, suggestions: List, suggestion_provenance: ProvenanceEnvelope):
        """Rank suggestions and send to UI"""
        await self._update_agent_status('ranking_agent', AgentStatus.WORKING, session_id)
        
        try:
            start_time = time.time()
            ranking_envelope = await asyncio.to_thread(
                self.ranking_agent.rank_suggestions,
                suggestions
            )
            processing_time = time.time() - start_time
            
            # Extract ranked suggestions from envelope
            ranked_suggestions = ranking_envelope.get('outputs', {}).get('ranked_suggestions', [])
            
            provenance = ProvenanceEnvelope(
                agent_id='ranking_agent',
                timestamp=datetime.now().timestamp(),
                inputs={'suggestions': suggestions},
                outputs=ranking_envelope.get('outputs', {}),
                confidence=ranking_envelope.get('confidence', 0.9),
                sources=ranking_envelope.get('sources', ['ranking_algorithm']),
                processing_time=processing_time
            )
            
            self.session_contexts[session_id]['provenance_chain'].append(provenance)
            
            # Publish final suggestions to UI
            await event_bus.publish(STREAMS['suggestions'], Event(
                type='suggestions_ready',
                session_id=session_id,
                agent_id='ranking_agent',
                data={
                    'suggestions': ranked_suggestions,
                    'provenance_chain': [p.to_dict() for p in self.session_contexts[session_id]['provenance_chain']],
                    'current_agent': 'ranking_agent'
                }
            ))
            
            await self._update_agent_status('ranking_agent', AgentStatus.COMPLETED, session_id)
            logger.info(f"✅ Generated and ranked {len(ranked_suggestions)} suggestions for session {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Suggestion ranking failed: {e}")
            await self._update_agent_status('ranking_agent', AgentStatus.ERROR, session_id)
    
    async def _update_agent_status(self, agent_name: str, status: str, session_id: str, data: Dict[str, Any] = None):
        """Update agent status and broadcast to UI"""
        self.agent_statuses[agent_name] = status
        
        # Prepare status data
        status_data = {
            'agent_name': agent_name,
            'status': status,
            'timestamp': datetime.now().timestamp()
        }
        
        # Include agent results data for completed status
        if status == AgentStatus.COMPLETED and data:
            status_data['results'] = data
        
        # Publish agent status update
        await event_bus.publish(STREAMS['agent_status'], Event(
            type='agent_status_update',
            session_id=session_id,
            agent_id=agent_name,
            data=status_data
        ))
        
        logger.debug(f"🔄 Agent {agent_name} status: {status}")
        if data and status == AgentStatus.COMPLETED:
            logger.debug(f"� Agent {agent_name} results included in status update")

# Global orchestrator instance
# Global orchestrator instance
orchestrator = EnhancedOrchestrator()
