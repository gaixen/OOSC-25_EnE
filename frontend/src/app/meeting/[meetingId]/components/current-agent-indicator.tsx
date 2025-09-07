"use client";

import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { ChevronDown, ChevronRight, Activity, Brain, Database, TrendingUp } from 'lucide-react';

interface AgentStatus {
  agent_name: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  timestamp: number;
  results?: any; // Contains the actual agent results data
}

interface CurrentAgentIndicatorProps {
  agentStatuses?: Record<string, AgentStatus>;
  currentAgent?: string;
}

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  'entity_extractor': 'Entity Extraction',
  'company_profile': 'Company Profile',
  'company_news': 'Company News',
  'market_competitor': 'Market Analysis',
  'person_enrichment': 'Person Enrichment',
  'suggestion_generator': 'AI Suggestion Generator',
  'ranking_agent': 'Suggestion Ranking'
};

const AGENT_ICONS: Record<string, any> = {
  'entity_extractor': Brain,
  'company_profile': Database,
  'company_news': TrendingUp,
  'market_competitor': Activity,
  'person_enrichment': Database,
  'suggestion_generator': Brain,
  'ranking_agent': TrendingUp
};

const STATUS_COLORS: Record<string, string> = {
  'idle': 'bg-gray-200 text-gray-700',
  'working': 'bg-blue-500 text-white animate-pulse',
  'completed': 'bg-green-500 text-white',
  'error': 'bg-red-500 text-white'
};

const STATUS_ICONS: Record<string, string> = {
  'idle': '⚪',
  'working': '🔄',
  'completed': '✅',
  'error': '❌'
};

// Helper component for rendering news articles with collapsible functionality
const NewsArticleList = ({ articles, sources, confidence, isCollapsible = false }: { 
  articles: any[], 
  sources?: string[], 
  confidence?: number, 
  isCollapsible?: boolean 
}) => {
  const [isNewsExpanded, setIsNewsExpanded] = useState(false);
  
  // Debug logging
  console.log('🔍 NewsArticleList Debug:', { 
    articles, 
    sources, 
    confidence, 
    isCollapsible,
    articlesLength: articles?.length 
  });
  
  if (!articles || articles.length === 0) {
    console.log('❌ NewsArticleList: No articles found');
    return null;
  }
  
  // Clean HTML from snippets and titles
  const cleanHtml = (html: string) => {
    if (!html) return '';
    return html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').trim();
  };
  
  if (isCollapsible) {
    return (
      <Collapsible open={isNewsExpanded} onOpenChange={setIsNewsExpanded}>
        <CollapsibleTrigger className="w-full">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-700 hover:text-blue-600 cursor-pointer py-1">
            <span>📰 Company News ({articles.length} articles)</span>
            {isNewsExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="mt-2 space-y-1 max-h-60 overflow-y-auto">
            <div className="space-y-2 pl-2">
              {articles.map((article, idx) => {
                console.log('🔍 Rendering article:', { idx, article });
                return (
                  <div key={idx} className="text-xs flex items-start gap-2">
                    <span className="text-blue-600 mt-1 font-bold">•</span>
                    <div className="flex-1">
                      <span className="text-gray-800 font-medium">
                        {cleanHtml(article.title)}
                      </span>
                      <span className="ml-2">
                        {article.url ? (
                          <a 
                            href={article.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline text-xs font-medium"
                            onClick={(e) => {
                              e.stopPropagation();
                              console.log('🔗 Clicking source link:', article.url);
                            }}
                          >
                            [Source]
                          </a>
                        ) : (
                          <span className="text-red-500 text-xs">[No URL]</span>
                        )}
                      </span>
                      {article.date && (
                        <div className="text-gray-500 text-xs mt-1">
                          {new Date(article.date).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Sources and Confidence at the end */}
            <div className="pt-3 mt-3 border-t border-gray-300 space-y-1">
              {sources && sources.length > 0 && (
                <div className="text-xs text-gray-600">
                  <span className="font-semibold">📊 Data Sources:</span> {sources.join(', ')}
                </div>
              )}
              {confidence !== undefined && (
                <div className="text-xs text-green-700 font-bold">
                  🎯 Confidence Score: {confidence.toFixed(2)}
                </div>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  }
  
  return (
    <div className="mt-2 space-y-1">
      <div className="text-xs font-semibold text-gray-600">📰 Recent News:</div>
      <div className="space-y-2 pl-2">
        {articles.slice(0, 5).map((article, idx) => (
          <div key={idx} className="text-xs flex items-start gap-2">
            <span className="text-blue-600 mt-1 font-bold">•</span>
            <div className="flex-1">
              <span className="text-gray-800 font-medium">
                {cleanHtml(article.title)}
              </span>
              <span className="ml-2">
                <a 
                  href={article.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline text-xs font-medium"
                >
                  [Source]
                </a>
              </span>
            </div>
          </div>
        ))}
      </div>
      
      {/* Sources and Confidence for non-collapsible version */}
      {(sources || confidence !== undefined) && (
        <div className="pt-3 mt-3 border-t border-gray-300 space-y-1">
          {sources && sources.length > 0 && (
            <div className="text-xs text-gray-600">
              <span className="font-semibold">📊 Sources:</span> {sources.join(', ')}
            </div>
          )}
          {confidence !== undefined && (
            <div className="text-xs text-green-700 font-bold">
              🎯 Confidence: {confidence.toFixed(2)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Helper component for rendering extracted entities
const ExtractedEntitiesList = ({ entities, sources, confidence, isCollapsible = false }: { 
  entities: any[], 
  sources?: string[], 
  confidence?: number, 
  isCollapsible?: boolean 
}) => {
  const [isEntitiesExpanded, setIsEntitiesExpanded] = useState(false);
  
  if (!entities || entities.length === 0) {
    return (
      <div className="text-xs text-gray-500 italic">
        No entities extracted
      </div>
    );
  }
  
  const getEntityIcon = (type: string) => {
    switch (type?.toUpperCase()) {
      case 'PERSON': return '👤';
      case 'ORG': 
      case 'ORGANIZATION': return '🏢';
      case 'LOCATION': return '📍';
      case 'MISC': return '🏷️';
      default: return '🔸';
    }
  };
  
  if (isCollapsible) {
    return (
      <Collapsible open={isEntitiesExpanded} onOpenChange={setIsEntitiesExpanded}>
        <CollapsibleTrigger className="w-full">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-700 hover:text-blue-600 cursor-pointer py-1">
            <span>🔍 Extracted Entities ({entities.length} found)</span>
            {isEntitiesExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="mt-2 space-y-1">
            <div className="space-y-1 pl-2">
              {entities.map((entity, idx) => (
                <div key={idx} className="text-xs flex items-start gap-2">
                  <span className="mt-1">{getEntityIcon(entity.type)}</span>
                  <div className="flex-1">
                    <span className="font-medium text-gray-800">
                      {entity.name}
                    </span>
                    <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                      {entity.type}
                    </span>
                    {entity.original_mentions && entity.original_mentions.length > 0 && (
                      <div className="text-gray-500 text-xs mt-1">
                        Mentioned as: {entity.original_mentions.join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Sources and Confidence */}
            <div className="pt-2 mt-2 border-t border-gray-200 space-y-1">
              {sources && sources.length > 0 && (
                <div className="text-xs text-gray-600">
                  <span className="font-semibold">Data Sources:</span> {sources.join(', ')}
                </div>
              )}
              {confidence !== undefined && (
                <div className="text-xs text-green-600 font-medium">
                  📊 Confidence Score: {confidence.toFixed(2)}
                </div>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  }
  
  return (
    <div className="mt-2 space-y-1">
      <div className="text-xs font-semibold text-gray-600">🔍 Extracted Entities:</div>
      <div className="space-y-1 pl-2">
        {entities.map((entity, idx) => (
          <div key={idx} className="text-xs flex items-start gap-2">
            <span className="mt-1">{getEntityIcon(entity.type)}</span>
            <div className="flex-1">
              <span className="font-medium text-gray-800">
                {entity.name}
              </span>
              <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium">
                {entity.type}
              </span>
            </div>
          </div>
        ))}
      </div>
      
      {/* Sources and Confidence for non-collapsible version */}
      {(sources || confidence !== undefined) && (
        <div className="pt-3 mt-3 border-t border-gray-300 space-y-1">
          {sources && sources.length > 0 && (
            <div className="text-xs text-gray-600">
              <span className="font-semibold">📊 Sources:</span> {sources.join(', ')}
            </div>
          )}
          {confidence !== undefined && (
            <div className="text-xs text-green-700 font-bold">
              🎯 Confidence: {confidence.toFixed(2)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Helper component for rendering person enrichment data with collapsible functionality
const PersonEnrichmentData = ({ 
  data, 
  sources, 
  confidence, 
  isCollapsible = false 
}: { 
  data: any, 
  sources?: string[], 
  confidence?: number, 
  isCollapsible?: boolean 
}) => {
  const [isPersonExpanded, setIsPersonExpanded] = useState(false);
  
  if (!data || !data.data) return null;
  
  const personData = data.data;
  
  if (isCollapsible) {
    return (
      <Collapsible open={isPersonExpanded} onOpenChange={setIsPersonExpanded}>
        <CollapsibleTrigger className="w-full">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-700 hover:text-blue-600 cursor-pointer py-1">
            <span>👤 Person Enrichment ({data.person_name})</span>
            {isPersonExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
            <div className="text-xs bg-white bg-opacity-70 p-3 rounded border shadow-sm space-y-2">
              {personData.email && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div><span className="font-medium">📧 Email:</span> {personData.email}</div>
                </div>
              )}
              {personData.position && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div><span className="font-medium">💼 Role:</span> {personData.position}</div>
                </div>
              )}
              {personData.wikipedia_summary && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div><span className="font-medium">📖 Bio:</span> {personData.wikipedia_summary.slice(0, 300)}...</div>
                </div>
              )}
              {personData.linkedin_profile && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div>
                    <a 
                      href={personData.linkedin_profile} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline text-xs font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      🔗 LinkedIn Profile
                    </a>
                  </div>
                </div>
              )}
              {personData.linkedin_search_url && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div>
                    <a 
                      href={personData.linkedin_search_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline text-xs font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      🔍 LinkedIn Search
                    </a>
                  </div>
                </div>
              )}
              {personData.ddg_results && personData.ddg_results.length > 0 && (
                <div className="space-y-1">
                  <div className="font-medium text-xs text-gray-700">🔍 Web Results:</div>
                  {personData.ddg_results.slice(0, 3).map((result: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-2">
                      <span className="text-blue-600 font-bold">•</span>
                      <div>
                        <a 
                          href={result.href} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 underline text-xs"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {result.title}
                        </a>
                        {result.body && (
                          <div className="text-gray-600 text-xs mt-1">{result.body.slice(0, 150)}...</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Sources and Confidence at the end */}
            <div className="pt-2 mt-2 border-t border-gray-200 space-y-1">
              {sources && sources.length > 0 && (
                <div className="text-xs text-gray-600">
                  <span className="font-semibold">Data Sources:</span> {sources.join(', ')}
                </div>
              )}
              {confidence !== undefined && (
                <div className="text-xs text-green-600 font-medium">
                  📊 Confidence Score: {confidence.toFixed(2)}
                </div>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  }
  
  return (
    <div className="mt-2 space-y-1">
      <div className="text-xs font-semibold text-gray-600">👤 Person Info:</div>
      <div className="text-xs bg-white bg-opacity-50 p-2 rounded border space-y-1">
        {personData.email && (
          <div><span className="font-medium">📧 Email:</span> {personData.email}</div>
        )}
        {personData.position && (
          <div><span className="font-medium">💼 Role:</span> {personData.position}</div>
        )}
        {personData.wikipedia_summary && (
          <div><span className="font-medium">📖 Bio:</span> {personData.wikipedia_summary.slice(0, 150)}...</div>
        )}
        {personData.linkedin_profile && (
          <a 
            href={personData.linkedin_profile} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline text-xs block"
            onClick={(e) => e.stopPropagation()}
          >
            🔗 LinkedIn Profile
          </a>
        )}
        {personData.linkedin_search_url && (
          <a 
            href={personData.linkedin_search_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline text-xs block"
            onClick={(e) => e.stopPropagation()}
          >
            🔍 LinkedIn Search
          </a>
        )}
        {personData.ddg_results && personData.ddg_results.length > 0 && (
          <div className="mt-1">
            <div className="font-medium text-xs mb-1">🔍 Web Results:</div>
            {personData.ddg_results.slice(0, 2).map((result: any, idx: number) => (
              <div key={idx} className="text-xs mb-1">
                <a 
                  href={result.href} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  {result.title}
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Sources and Confidence for non-collapsible version */}
      {(sources || confidence !== undefined) && (
        <div className="pt-2 mt-2 border-t border-gray-200 space-y-1">
          {sources && sources.length > 0 && (
            <div className="text-xs text-gray-600">
              <span className="font-semibold">Sources:</span> {sources.join(', ')}
            </div>
          )}
          {confidence !== undefined && (
            <div className="text-xs text-green-600 font-medium">
              📊 Confidence: {confidence.toFixed(2)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Helper component for rendering company profile data with collapsible functionality
const CompanyProfileData = ({ 
  data, 
  sources, 
  confidence, 
  isCollapsible = false 
}: { 
  data: any, 
  sources?: string[], 
  confidence?: number, 
  isCollapsible?: boolean 
}) => {
  const [isCompanyExpanded, setIsCompanyExpanded] = useState(false);
  
  if (!data || !data.data) return null;
  
  const companyData = data.data;
  
  if (isCollapsible) {
    return (
      <Collapsible open={isCompanyExpanded} onOpenChange={setIsCompanyExpanded}>
        <CollapsibleTrigger className="w-full">
          <div className="flex items-center justify-between text-xs font-semibold text-gray-700 hover:text-blue-600 cursor-pointer py-1">
            <span>🏢 Company Profile ({data.company_name})</span>
            {isCompanyExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="mt-2 space-y-2 max-h-60 overflow-y-auto">
            <div className="text-xs bg-white bg-opacity-70 p-3 rounded border shadow-sm space-y-2">
              {companyData.description && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div><span className="font-medium">📝 Description:</span> {companyData.description}</div>
                </div>
              )}
              {companyData.website && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div>
                    <a 
                      href={companyData.website} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline text-xs font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      🌐 Company Website
                    </a>
                  </div>
                </div>
              )}
              {companyData.linkedin_url && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div>
                    <a 
                      href={companyData.linkedin_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 underline text-xs font-medium"
                      onClick={(e) => e.stopPropagation()}
                    >
                      🔗 Company LinkedIn
                    </a>
                  </div>
                </div>
              )}
              {companyData.industry && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div><span className="font-medium">🏭 Industry:</span> {companyData.industry}</div>
                </div>
              )}
              {companyData.size && (
                <div className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">•</span>
                  <div><span className="font-medium">👥 Size:</span> {companyData.size}</div>
                </div>
              )}
            </div>
            
            {/* Sources and Confidence at the end */}
            <div className="pt-2 mt-2 border-t border-gray-200 space-y-1">
              {sources && sources.length > 0 && (
                <div className="text-xs text-gray-600">
                  <span className="font-semibold">Data Sources:</span> {sources.join(', ')}
                </div>
              )}
              {confidence !== undefined && (
                <div className="text-xs text-green-600 font-medium">
                  📊 Confidence Score: {confidence.toFixed(2)}
                </div>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  }
  
  return (
    <div className="mt-2 space-y-1">
      <div className="text-xs font-semibold text-gray-600">🏢 Company Info:</div>
      <div className="text-xs bg-white bg-opacity-50 p-2 rounded border space-y-1">
        {companyData.description && (
          <div><span className="font-medium">📝 Description:</span> {companyData.description.slice(0, 150)}...</div>
        )}
        {companyData.website && (
          <a 
            href={companyData.website} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline text-xs block"
          >
            🌐 Company Website
          </a>
        )}
        {companyData.linkedin_url && (
          <a 
            href={companyData.linkedin_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline text-xs block"
          >
            🔗 Company LinkedIn
          </a>
        )}
      </div>
      
      {/* Sources and Confidence for non-collapsible version */}
      {(sources || confidence !== undefined) && (
        <div className="pt-2 mt-2 border-t border-gray-200 space-y-1">
          {sources && sources.length > 0 && (
            <div className="text-xs text-gray-600">
              <span className="font-semibold">Sources:</span> {sources.join(', ')}
            </div>
          )}
          {confidence !== undefined && (
            <div className="text-xs text-green-600 font-medium">
              📊 Confidence: {confidence.toFixed(2)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export function CurrentAgentIndicator({ agentStatuses = {}, currentAgent }: CurrentAgentIndicatorProps) {
  const [workingAgents, setWorkingAgents] = useState<string[]>([]);
  const [isExpanded, setIsExpanded] = useState(true);
  
  useEffect(() => {
    if (!agentStatuses) return;
    
    const working = Object.keys(agentStatuses).filter(
      agent => agentStatuses[agent]?.status === 'working'
    );
    setWorkingAgents(working);
    
    // Auto-expand when agents are working
    if (working.length > 0) {
      setIsExpanded(true);
    }
  }, [agentStatuses]);

  const getAgentProgress = () => {
    if (!agentStatuses) return 0;
    
    const totalAgents = Object.keys(AGENT_DISPLAY_NAMES).length;
    const completedAgents = Object.keys(agentStatuses).filter(
      agent => agentStatuses[agent]?.status === 'completed'
    ).length;
    return (completedAgents / totalAgents) * 100;
  };

  const getCurrentlyWorkingAgent = () => {
    if (currentAgent && agentStatuses && agentStatuses[currentAgent]?.status === 'working') {
      return currentAgent;
    }
    return workingAgents[0];
  };

  const activeAgent = getCurrentlyWorkingAgent();
  const hasActivity = agentStatuses && Object.keys(agentStatuses).length > 0;

  return (
    <Card className="w-full">
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger className="w-full">
          <CardHeader className="pb-3 cursor-pointer hover:bg-gray-50 transition-colors">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <div className="flex items-center gap-2">
                🤖 AI Agent Pipeline
                {workingAgents.length > 0 && (
                  <Badge variant="secondary" className="text-xs animate-pulse">
                    {workingAgents.length} active
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                {hasActivity && (
                  <div className="text-xs text-gray-500">
                    {Math.round(getAgentProgress())}%
                  </div>
                )}
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </div>
            </CardTitle>
          </CardHeader>
        </CollapsibleTrigger>
        
        <CollapsibleContent>
          <CardContent className="space-y-4 pt-0">
            {/* Current Active Agent */}
            {activeAgent && (
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1 bg-blue-200 rounded">
                    {React.createElement(AGENT_ICONS[activeAgent] || Brain, {
                      className: "h-4 w-4 text-blue-600"
                    })}
                  </div>
                  <span className="font-medium text-blue-900">Currently Processing</span>
                </div>
                <div className="text-blue-800 font-semibold">
                  {AGENT_DISPLAY_NAMES[activeAgent] || activeAgent}
                </div>
                <div className="text-xs text-blue-600 mt-1">
                  Gathering intelligence...
                </div>
              </div>
            )}

            {/* Overall Progress */}
            {hasActivity && (
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-gray-600">
                  <span>Pipeline Progress</span>
                  <span>{Math.round(getAgentProgress())}%</span>
                </div>
                <Progress value={getAgentProgress()} className="h-2" />
              </div>
            )}

            {/* Agent Status List */}
            <div className="space-y-2">
              <div className="text-xs font-medium text-gray-600 uppercase tracking-wider">
                Agent Status & Results
              </div>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(AGENT_DISPLAY_NAMES).map(([agentKey, displayName]) => {
                  const status = agentStatuses?.[agentKey];
                  const statusKey = status?.status || 'idle';
                  const IconComponent = AGENT_ICONS[agentKey] || Brain;
                  const hasResults = status?.results;
                  
                  return (
                    <div key={agentKey} className="space-y-1">
                      <div 
                        className={`flex items-center justify-between p-2 rounded text-xs transition-all duration-200 ${
                          STATUS_COLORS[statusKey]
                        } ${statusKey === 'working' ? 'shadow-md transform scale-105' : ''}`}
                      >
                        <div className="flex items-center gap-2">
                          <IconComponent className="h-3 w-3" />
                          <span className="font-medium">{displayName}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span>{STATUS_ICONS[statusKey]}</span>
                          <span className="text-xs opacity-75 capitalize">
                            {statusKey}
                          </span>
                        </div>
                      </div>
                      
                      {/* Show results data for completed agents */}
                      {hasResults && statusKey === 'completed' && (
                        <div className="ml-1 mr-1 bg-gray-50 bg-opacity-50 rounded p-2">
                          {agentKey === 'entity_extractor' && status.results?.extracted_entities && (
                            <ExtractedEntitiesList 
                              entities={status.results.extracted_entities} 
                              sources={status.results.sources}
                              confidence={status.results.confidence}
                              isCollapsible={true} 
                            />
                          )}
                          {agentKey === 'company_news' && status.results?.data && (
                            <>
                              {console.log('🔍 Company News Debug:', { agentKey, status: status.results })}
                              <NewsArticleList 
                                articles={status.results.data} 
                                sources={status.results.sources}
                                confidence={status.results.confidence}
                                isCollapsible={true} 
                              />
                            </>
                          )}
                          {agentKey === 'person_enrichment' && status.results && (
                            <PersonEnrichmentData 
                              data={status.results} 
                              sources={status.results.sources}
                              confidence={status.results.confidence}
                              isCollapsible={true} 
                            />
                          )}
                          {agentKey === 'company_profile' && status.results && (
                            <CompanyProfileData 
                              data={status.results} 
                              sources={status.results.sources}
                              confidence={status.results.confidence}
                              isCollapsible={true} 
                            />
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Processing Details */}
            {hasActivity && (
              <div className="text-xs text-gray-500 pt-2 border-t space-y-1">
                <div className="flex items-center justify-between">
                  <span>📊 Real-time Intelligence</span>
                  <Badge variant="outline" className="text-xs">
                    Live
                  </Badge>
                </div>
                {workingAgents.length > 0 && (
                  <div className="text-green-600">
                    ⚡ {workingAgents.length} agent(s) processing in parallel
                  </div>
                )}
              </div>
            )}

            {/* No Activity State */}
            {!hasActivity && (
              <div className="text-center py-4 text-gray-500">
                <Brain className="h-6 w-6 mx-auto mb-2 opacity-50" />
                <div className="text-xs">
                  Ready to process voice input
                </div>
              </div>
            )}
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
