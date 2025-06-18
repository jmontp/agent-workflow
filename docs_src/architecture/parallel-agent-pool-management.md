# Parallel Agent Pool Management and Resource Allocation

## Executive Summary

This document specifies the agent pool management and resource allocation system for parallel TDD execution. The system provides dynamic scaling, intelligent load balancing, and optimal resource utilization across concurrent TDD cycles while maintaining agent security boundaries and quality standards.

## Agent Pool Architecture

### 1. Multi-Tier Pool Structure

```python
class AgentPoolManager:
    """Central manager for all agent pools with sophisticated allocation"""
    
    def __init__(self, config: PoolManagerConfig):
        self.pools = {
            AgentType.DESIGN: DynamicAgentPool(AgentType.DESIGN, config.design_pool),
            AgentType.QA: DynamicAgentPool(AgentType.QA, config.qa_pool),
            AgentType.CODE: DynamicAgentPool(AgentType.CODE, config.code_pool),
            AgentType.DATA: DynamicAgentPool(AgentType.DATA, config.data_pool)
        }
        self.resource_allocator = ResourceAllocator(config.resource_limits)
        self.load_balancer = AgentLoadBalancer()
        self.metrics_collector = PoolMetricsCollector()
        self.scaler = AutoScaler(config.scaling_policies)
        
    async def acquire_agent(
        self, 
        agent_type: AgentType, 
        cycle_id: str,
        requirements: AgentRequirements,
        timeout: int = 30
    ) -> AgentAllocation:
        """Acquire agent with specific requirements for a cycle"""
        
        # Check resource availability
        resource_check = await self.resource_allocator.check_availability(
            agent_type, requirements
        )
        if not resource_check.available:
            raise ResourceExhausted(f"Insufficient resources for {agent_type}")
            
        # Get agent from pool
        pool = self.pools[agent_type]
        
        try:
            # Try to acquire from pool
            agent = await asyncio.wait_for(
                pool.acquire_with_requirements(cycle_id, requirements),
                timeout=timeout
            )
            
            # Allocate resources
            allocation = await self.resource_allocator.allocate(
                agent, cycle_id, requirements
            )
            
            # Record metrics
            await self.metrics_collector.record_acquisition(
                agent_type, cycle_id, allocation
            )
            
            return AgentAllocation(
                agent=agent,
                allocation=allocation,
                acquired_at=datetime.now(),
                cycle_id=cycle_id
            )
            
        except asyncio.TimeoutError:
            # Try scaling up pool
            if await self.scaler.can_scale_up(agent_type):
                await self.scaler.scale_up(agent_type, 1)
                # Retry once after scaling
                agent = await asyncio.wait_for(
                    pool.acquire_with_requirements(cycle_id, requirements),
                    timeout=timeout // 2
                )
                allocation = await self.resource_allocator.allocate(
                    agent, cycle_id, requirements
                )
                return AgentAllocation(agent=agent, allocation=allocation, 
                                     acquired_at=datetime.now(), cycle_id=cycle_id)
            else:
                raise AgentPoolExhausted(f"No {agent_type} agents available")

@dataclass
class AgentRequirements:
    """Requirements for agent allocation"""
    memory_mb: int = 1024
    cpu_cores: float = 1.0
    token_budget: int = 50000
    disk_space_mb: int = 500
    network_access: bool = True
    special_tools: List[str] = field(default_factory=list)
    security_level: SecurityLevel = SecurityLevel.STANDARD
    isolation_level: IsolationLevel = IsolationLevel.PROCESS
    
class DynamicAgentPool:
    """Self-managing pool of agents with dynamic scaling"""
    
    def __init__(self, agent_type: AgentType, config: PoolConfig):
        self.agent_type = agent_type
        self.config = config
        self.available_agents: asyncio.Queue = asyncio.Queue(maxsize=config.max_size)
        self.busy_agents: Dict[str, AgentInstance] = {}
        self.standby_agents: Dict[str, AgentInstance] = {}
        self.metrics = PoolMetrics()
        self.health_monitor = AgentHealthMonitor(self)
        
    async def acquire_with_requirements(
        self, 
        cycle_id: str, 
        requirements: AgentRequirements
    ) -> AgentInstance:
        """Acquire agent that meets specific requirements"""
        
        # Try to find suitable agent in available pool
        suitable_agent = await self._find_suitable_agent(requirements)
        
        if suitable_agent:
            # Configure agent for requirements
            await self._configure_agent(suitable_agent, requirements)
            self.busy_agents[cycle_id] = suitable_agent
            self.metrics.record_acquisition()
            return suitable_agent
            
        # No suitable agent - try to create one
        if await self._can_create_agent():
            new_agent = await self._create_agent(requirements)
            await self._configure_agent(new_agent, requirements)
            self.busy_agents[cycle_id] = new_agent
            self.metrics.record_acquisition()
            return new_agent
            
        # Wait for agent to become available
        return await self._wait_for_suitable_agent(cycle_id, requirements)
        
    async def _find_suitable_agent(self, requirements: AgentRequirements) -> Optional[AgentInstance]:
        """Find agent that meets requirements from available pool"""
        # Check available agents
        available_list = []
        while not self.available_agents.empty():
            try:
                agent = self.available_agents.get_nowait()
                available_list.append(agent)
            except asyncio.QueueEmpty:
                break
                
        suitable_agent = None
        for agent in available_list:
            if await self._agent_meets_requirements(agent, requirements):
                suitable_agent = agent
                break
            else:
                # Put back in queue
                await self.available_agents.put(agent)
                
        return suitable_agent
        
    async def _agent_meets_requirements(
        self, 
        agent: AgentInstance, 
        requirements: AgentRequirements
    ) -> bool:
        """Check if agent can meet the requirements"""
        # Check resource capacity
        if agent.max_memory_mb < requirements.memory_mb:
            return False
        if agent.max_cpu_cores < requirements.cpu_cores:
            return False
        if agent.max_token_budget < requirements.token_budget:
            return False
            
        # Check security constraints
        if agent.security_level.value < requirements.security_level.value:
            return False
            
        # Check tool availability
        available_tools = set(agent.available_tools)
        required_tools = set(requirements.special_tools)
        if not required_tools.issubset(available_tools):
            return False
            
        return True
        
    async def _create_agent(self, requirements: AgentRequirements) -> AgentInstance:
        """Create new agent instance optimized for requirements"""
        agent_config = AgentConfig(
            agent_type=self.agent_type,
            memory_mb=max(requirements.memory_mb, self.config.default_memory),
            cpu_cores=max(requirements.cpu_cores, self.config.default_cpu),
            token_budget=max(requirements.token_budget, self.config.default_tokens),
            security_level=requirements.security_level,
            isolation_level=requirements.isolation_level,
            enabled_tools=self._get_tools_for_type(self.agent_type) + requirements.special_tools
        )
        
        agent = await AgentFactory.create_agent(agent_config)
        await agent.initialize()
        
        return agent
```

### 2. Intelligent Load Balancing

```python
class AgentLoadBalancer:
    """Intelligent load balancing across agent pools"""
    
    def __init__(self):
        self.load_algorithms = {
            LoadBalancingStrategy.ROUND_ROBIN: RoundRobinBalancer(),
            LoadBalancingStrategy.LEAST_LOADED: LeastLoadedBalancer(),
            LoadBalancingStrategy.WORKLOAD_AWARE: WorkloadAwareBalancer(),
            LoadBalancingStrategy.PREDICTIVE: PredictiveBalancer()
        }
        self.current_strategy = LoadBalancingStrategy.WORKLOAD_AWARE
        
    async def select_optimal_agent(
        self, 
        agent_type: AgentType,
        cycle_context: CycleContext,
        available_agents: List[AgentInstance]
    ) -> AgentInstance:
        """Select optimal agent based on current strategy and context"""
        
        balancer = self.load_algorithms[self.current_strategy]
        
        # Score all available agents
        agent_scores = []
        for agent in available_agents:
            score = await balancer.score_agent(agent, cycle_context)
            agent_scores.append((agent, score))
            
        # Select highest scoring agent
        if agent_scores:
            best_agent, best_score = max(agent_scores, key=lambda x: x[1])
            return best_agent
        else:
            raise NoSuitableAgent("No agents meet the requirements")

class WorkloadAwareBalancer:
    """Load balancer that considers workload characteristics"""
    
    async def score_agent(
        self, 
        agent: AgentInstance, 
        cycle_context: CycleContext
    ) -> float:
        """Score agent based on workload suitability"""
        score = 0.0
        
        # Current load factor (lower is better)
        load_factor = await self._calculate_load_factor(agent)
        score += (1.0 - load_factor) * 0.3
        
        # Specialization match
        specialization_score = await self._calculate_specialization_match(
            agent, cycle_context
        )
        score += specialization_score * 0.25
        
        # Resource availability
        resource_score = await self._calculate_resource_availability(
            agent, cycle_context.requirements
        )
        score += resource_score * 0.2
        
        # Historical performance
        performance_score = await self._get_historical_performance(
            agent, cycle_context.story_type
        )
        score += performance_score * 0.15
        
        # Context affinity (worked on similar code recently)
        context_score = await self._calculate_context_affinity(
            agent, cycle_context
        )
        score += context_score * 0.1
        
        return score
        
    async def _calculate_specialization_match(
        self, 
        agent: AgentInstance, 
        cycle_context: CycleContext
    ) -> float:
        """Calculate how well agent's specialization matches the workload"""
        agent_specializations = agent.get_specializations()
        workload_tags = cycle_context.story.tags
        
        # Calculate overlap between agent skills and workload requirements
        if not workload_tags:
            return 0.5  # Neutral score for untagged work
            
        skill_overlap = len(set(agent_specializations) & set(workload_tags))
        max_possible_overlap = len(workload_tags)
        
        return skill_overlap / max_possible_overlap if max_possible_overlap > 0 else 0.0

class PredictiveBalancer:
    """ML-based predictive load balancing"""
    
    def __init__(self):
        self.performance_predictor = AgentPerformancePredictor()
        self.completion_time_model = CompletionTimeModel()
        
    async def score_agent(
        self, 
        agent: AgentInstance, 
        cycle_context: CycleContext
    ) -> float:
        """Score based on predicted performance"""
        
        # Predict task completion time
        predicted_time = await self.completion_time_model.predict(
            agent, cycle_context
        )
        
        # Predict success probability
        success_probability = await self.performance_predictor.predict_success(
            agent, cycle_context
        )
        
        # Predict resource efficiency
        efficiency_score = await self.performance_predictor.predict_efficiency(
            agent, cycle_context
        )
        
        # Combine predictions into overall score
        # Favor agents with shorter predicted times, higher success rate, better efficiency
        time_score = 1.0 / (1.0 + predicted_time.total_seconds() / 3600)  # Normalize by hours
        
        overall_score = (
            success_probability * 0.4 +
            efficiency_score * 0.3 +
            time_score * 0.3
        )
        
        return overall_score
```

### 3. Advanced Auto-Scaling

```python
class AutoScaler:
    """Sophisticated auto-scaling for agent pools"""
    
    def __init__(self, scaling_policies: Dict[AgentType, ScalingPolicy]):
        self.policies = scaling_policies
        self.metrics_analyzer = ScalingMetricsAnalyzer()
        self.predictive_scaler = PredictiveScaler()
        self.scaling_history: List[ScalingEvent] = []
        
    async def evaluate_scaling_needs(self) -> List[ScalingDecision]:
        """Evaluate scaling needs for all pools"""
        decisions = []
        
        for agent_type, policy in self.policies.items():
            current_metrics = await self.metrics_analyzer.get_current_metrics(agent_type)
            decision = await self._evaluate_pool_scaling(agent_type, policy, current_metrics)
            
            if decision.action != ScalingAction.NO_ACTION:
                decisions.append(decision)
                
        return decisions
        
    async def _evaluate_pool_scaling(
        self, 
        agent_type: AgentType, 
        policy: ScalingPolicy,
        metrics: PoolMetrics
    ) -> ScalingDecision:
        """Evaluate scaling for a specific pool"""
        
        # Current state analysis
        utilization = metrics.utilization
        wait_time = metrics.average_wait_time
        queue_depth = metrics.queue_depth
        current_size = metrics.pool_size
        
        # Predictive analysis
        future_demand = await self.predictive_scaler.predict_demand(
            agent_type, look_ahead_minutes=30
        )
        
        # Decision logic
        if (utilization > policy.scale_up_threshold and 
            wait_time > policy.max_acceptable_wait_time and
            current_size < policy.max_size):
            
            # Calculate scale-up amount
            target_size = await self._calculate_optimal_scale_up(
                agent_type, current_size, metrics, future_demand
            )
            
            return ScalingDecision(
                agent_type=agent_type,
                action=ScalingAction.SCALE_UP,
                current_size=current_size,
                target_size=target_size,
                reason=f"High utilization ({utilization:.2f}) and wait time ({wait_time:.1f}s)",
                confidence=await self._calculate_scaling_confidence(metrics, future_demand)
            )
            
        elif (utilization < policy.scale_down_threshold and 
              wait_time < policy.min_useful_wait_time and
              current_size > policy.min_size and
              await self._can_safely_scale_down(agent_type)):
            
            target_size = await self._calculate_optimal_scale_down(
                agent_type, current_size, metrics, future_demand
            )
            
            return ScalingDecision(
                agent_type=agent_type,
                action=ScalingAction.SCALE_DOWN,
                current_size=current_size,
                target_size=target_size,
                reason=f"Low utilization ({utilization:.2f}) and short wait times",
                confidence=await self._calculate_scaling_confidence(metrics, future_demand)
            )
            
        return ScalingDecision(
            agent_type=agent_type,
            action=ScalingAction.NO_ACTION,
            current_size=current_size,
            target_size=current_size,
            reason="Metrics within acceptable range"
        )
        
    async def _calculate_optimal_scale_up(
        self,
        agent_type: AgentType,
        current_size: int,
        metrics: PoolMetrics,
        future_demand: DemandPrediction
    ) -> int:
        """Calculate optimal scale-up target"""
        
        # Base calculation using Little's Law
        # Target pool size = arrival rate × service time / target utilization
        arrival_rate = metrics.request_rate_per_minute
        service_time_minutes = metrics.average_service_time.total_seconds() / 60
        target_utilization = 0.75  # Target 75% utilization
        
        base_target = math.ceil((arrival_rate * service_time_minutes) / target_utilization)
        
        # Adjust for predicted demand changes
        demand_multiplier = future_demand.peak_demand_ratio
        adjusted_target = math.ceil(base_target * demand_multiplier)
        
        # Apply policy constraints
        policy = self.policies[agent_type]
        max_increase = math.ceil(current_size * policy.max_scale_up_ratio)
        target_size = min(adjusted_target, current_size + max_increase, policy.max_size)
        
        return max(target_size, current_size + 1)  # Scale up by at least 1

class PredictiveScaler:
    """ML-based predictive scaling"""
    
    def __init__(self):
        self.demand_model = DemandPredictionModel()
        self.seasonal_analyzer = SeasonalPatternAnalyzer()
        self.event_detector = WorkloadEventDetector()
        
    async def predict_demand(
        self, 
        agent_type: AgentType, 
        look_ahead_minutes: int
    ) -> DemandPrediction:
        """Predict future demand for agent type"""
        
        # Historical pattern analysis
        historical_pattern = await self.seasonal_analyzer.get_pattern(
            agent_type, look_ahead_minutes
        )
        
        # Event-based prediction (e.g., large story batches)
        event_impact = await self.event_detector.predict_events(
            agent_type, look_ahead_minutes
        )
        
        # ML model prediction
        ml_prediction = await self.demand_model.predict(
            agent_type, look_ahead_minutes
        )
        
        # Combine predictions
        base_demand = ml_prediction.base_demand
        seasonal_multiplier = historical_pattern.seasonal_multiplier
        event_multiplier = event_impact.impact_multiplier
        
        predicted_demand = base_demand * seasonal_multiplier * event_multiplier
        
        return DemandPrediction(
            agent_type=agent_type,
            time_horizon_minutes=look_ahead_minutes,
            predicted_demand=predicted_demand,
            base_demand=base_demand,
            seasonal_multiplier=seasonal_multiplier,
            event_multiplier=event_multiplier,
            confidence=min(ml_prediction.confidence, 
                          historical_pattern.confidence, 
                          event_impact.confidence),
            peak_demand_ratio=max(seasonal_multiplier, event_multiplier)
        )
```

## Resource Allocation System

### 1. Multi-Resource Allocation

```python
class ResourceAllocator:
    """Sophisticated resource allocation across multiple dimensions"""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.allocations: Dict[str, ResourceAllocation] = {}  # cycle_id -> allocation
        self.global_usage = GlobalResourceUsage()
        self.allocation_optimizer = AllocationOptimizer()
        
    async def allocate(
        self, 
        agent: AgentInstance, 
        cycle_id: str,
        requirements: AgentRequirements
    ) -> ResourceAllocation:
        """Allocate resources for agent in cycle"""
        
        # Check if allocation is feasible
        feasibility = await self._check_allocation_feasibility(requirements)
        if not feasibility.feasible:
            raise ResourceAllocationError(feasibility.reason)
            
        # Optimize allocation within constraints
        optimized_allocation = await self.allocation_optimizer.optimize(
            requirements, self.global_usage, self.limits
        )
        
        # Reserve resources
        allocation = ResourceAllocation(
            cycle_id=cycle_id,
            agent_id=agent.id,
            memory_mb=optimized_allocation.memory_mb,
            cpu_cores=optimized_allocation.cpu_cores,
            token_budget=optimized_allocation.token_budget,
            disk_space_mb=optimized_allocation.disk_space_mb,
            network_bandwidth_mbps=optimized_allocation.network_bandwidth,
            allocated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=4)  # Default 4-hour allocation
        )
        
        # Update global usage
        await self.global_usage.reserve(allocation)
        self.allocations[cycle_id] = allocation
        
        # Configure agent with allocation
        await agent.configure_resources(allocation)
        
        return allocation
        
    async def _check_allocation_feasibility(
        self, 
        requirements: AgentRequirements
    ) -> AllocationFeasibility:
        """Check if requested allocation is feasible"""
        
        # Check individual resource limits
        if requirements.memory_mb > self.limits.max_memory_per_agent:
            return AllocationFeasibility(
                feasible=False, 
                reason=f"Memory request {requirements.memory_mb}MB exceeds limit {self.limits.max_memory_per_agent}MB"
            )
            
        if requirements.cpu_cores > self.limits.max_cpu_per_agent:
            return AllocationFeasibility(
                feasible=False,
                reason=f"CPU request {requirements.cpu_cores} exceeds limit {self.limits.max_cpu_per_agent}"
            )
            
        # Check global resource availability
        available_memory = self.limits.total_memory_mb - self.global_usage.used_memory_mb
        if requirements.memory_mb > available_memory:
            return AllocationFeasibility(
                feasible=False,
                reason=f"Insufficient memory: need {requirements.memory_mb}MB, available {available_memory}MB"
            )
            
        available_cpu = self.limits.total_cpu_cores - self.global_usage.used_cpu_cores
        if requirements.cpu_cores > available_cpu:
            return AllocationFeasibility(
                feasible=False,
                reason=f"Insufficient CPU: need {requirements.cpu_cores}, available {available_cpu}"
            )
            
        return AllocationFeasibility(feasible=True)

class AllocationOptimizer:
    """Optimize resource allocations for efficiency"""
    
    async def optimize(
        self,
        requirements: AgentRequirements,
        current_usage: GlobalResourceUsage,
        limits: ResourceLimits
    ) -> OptimizedAllocation:
        """Optimize allocation within constraints"""
        
        # Start with requested amounts
        allocation = OptimizedAllocation(
            memory_mb=requirements.memory_mb,
            cpu_cores=requirements.cpu_cores,
            token_budget=requirements.token_budget,
            disk_space_mb=requirements.disk_space_mb,
            network_bandwidth=10.0  # Default bandwidth
        )
        
        # Apply memory optimization
        allocation.memory_mb = await self._optimize_memory_allocation(
            requirements.memory_mb, current_usage, limits
        )
        
        # Apply CPU optimization  
        allocation.cpu_cores = await self._optimize_cpu_allocation(
            requirements.cpu_cores, current_usage, limits
        )
        
        # Apply token budget optimization
        allocation.token_budget = await self._optimize_token_allocation(
            requirements.token_budget, current_usage, limits
        )
        
        return allocation
        
    async def _optimize_memory_allocation(
        self,
        requested_mb: int,
        current_usage: GlobalResourceUsage,
        limits: ResourceLimits
    ) -> int:
        """Optimize memory allocation"""
        
        # Calculate available memory
        available_mb = limits.total_memory_mb - current_usage.used_memory_mb
        
        # If we have plenty of memory, potentially give more than requested
        memory_utilization = current_usage.used_memory_mb / limits.total_memory_mb
        
        if memory_utilization < 0.6:  # Low utilization
            # Give up to 50% more memory for better performance
            optimized_mb = min(
                int(requested_mb * 1.5),
                available_mb,
                limits.max_memory_per_agent
            )
        elif memory_utilization < 0.8:  # Medium utilization
            # Give exactly what was requested
            optimized_mb = min(requested_mb, available_mb)
        else:  # High utilization
            # Try to reduce allocation if possible
            optimized_mb = min(
                max(int(requested_mb * 0.8), limits.min_memory_per_agent),
                available_mb
            )
            
        return optimized_mb
```

### 2. Dynamic Resource Rebalancing

```python
class ResourceRebalancer:
    """Dynamic rebalancing of resources across active cycles"""
    
    def __init__(self, allocator: ResourceAllocator):
        self.allocator = allocator
        self.usage_monitor = ResourceUsageMonitor()
        self.rebalancing_history: List[RebalancingEvent] = []
        
    async def rebalance_resources(self) -> RebalancingResult:
        """Rebalance resources across all active allocations"""
        
        # Analyze current usage patterns
        usage_analysis = await self.usage_monitor.analyze_current_usage()
        
        # Identify rebalancing opportunities
        opportunities = await self._identify_rebalancing_opportunities(usage_analysis)
        
        if not opportunities:
            return RebalancingResult(
                rebalanced=False,
                reason="No beneficial rebalancing opportunities found"
            )
            
        # Execute rebalancing
        results = []
        for opportunity in opportunities:
            result = await self._execute_rebalancing(opportunity)
            results.append(result)
            
        return RebalancingResult(
            rebalanced=True,
            opportunities_found=len(opportunities),
            successful_rebalances=sum(1 for r in results if r.success),
            total_resources_freed=sum(r.resources_freed for r in results),
            estimated_performance_improvement=await self._calculate_improvement(results)
        )
        
    async def _identify_rebalancing_opportunities(
        self, 
        usage_analysis: UsageAnalysis
    ) -> List[RebalancingOpportunity]:
        """Identify opportunities for resource rebalancing"""
        opportunities = []
        
        # Find over-allocated cycles (using much less than allocated)
        for cycle_id, usage in usage_analysis.cycle_usage.items():
            allocation = self.allocator.allocations.get(cycle_id)
            if not allocation:
                continue
                
            # Memory over-allocation
            if usage.memory_utilization < 0.3:  # Using less than 30% of allocated memory
                memory_to_free = int(allocation.memory_mb * 0.4)  # Free 40% of allocation
                opportunities.append(RebalancingOpportunity(
                    type=RebalancingType.MEMORY_REDUCTION,
                    cycle_id=cycle_id,
                    current_allocation=allocation.memory_mb,
                    suggested_allocation=allocation.memory_mb - memory_to_free,
                    freed_amount=memory_to_free,
                    confidence=0.8
                ))
                
            # CPU over-allocation
            if usage.cpu_utilization < 0.25:  # Using less than 25% of allocated CPU
                cpu_to_free = allocation.cpu_cores * 0.3
                opportunities.append(RebalancingOpportunity(
                    type=RebalancingType.CPU_REDUCTION,
                    cycle_id=cycle_id,
                    current_allocation=allocation.cpu_cores,
                    suggested_allocation=allocation.cpu_cores - cpu_to_free,
                    freed_amount=cpu_to_free,
                    confidence=0.7
                ))
                
        # Find under-allocated cycles (need more resources)
        for cycle_id, usage in usage_analysis.cycle_usage.items():
            if usage.memory_pressure > 0.9:  # Memory pressure
                additional_memory = int(usage.current_memory_mb * 0.5)
                opportunities.append(RebalancingOpportunity(
                    type=RebalancingType.MEMORY_INCREASE,
                    cycle_id=cycle_id,
                    current_allocation=usage.current_memory_mb,
                    suggested_allocation=usage.current_memory_mb + additional_memory,
                    needed_amount=additional_memory,
                    confidence=0.9
                ))
                
        return sorted(opportunities, key=lambda o: o.confidence, reverse=True)
```

## Performance Monitoring and Optimization

### 1. Comprehensive Pool Metrics

```python
class PoolMetricsCollector:
    """Collect comprehensive metrics for agent pools"""
    
    def __init__(self):
        self.metrics_store = TimeSeriesMetricsStore()
        self.realtime_metrics: Dict[AgentType, PoolMetrics] = {}
        self.collection_interval = 30  # seconds
        
    async def collect_pool_metrics(self, agent_type: AgentType) -> PoolMetrics:
        """Collect current metrics for a pool"""
        pool = self._get_pool(agent_type)
        
        metrics = PoolMetrics(
            agent_type=agent_type,
            timestamp=datetime.now(),
            
            # Pool size metrics
            total_agents=pool.total_agent_count(),
            available_agents=pool.available_agent_count(),
            busy_agents=pool.busy_agent_count(),
            standby_agents=pool.standby_agent_count(),
            
            # Utilization metrics
            utilization=pool.busy_agent_count() / max(pool.total_agent_count(), 1),
            queue_depth=pool.queue_depth(),
            average_wait_time=await pool.calculate_average_wait_time(),
            
            # Performance metrics
            request_rate_per_minute=await self._calculate_request_rate(agent_type),
            completion_rate_per_minute=await self._calculate_completion_rate(agent_type),
            average_service_time=await self._calculate_average_service_time(agent_type),
            
            # Quality metrics
            success_rate=await self._calculate_success_rate(agent_type),
            error_rate=await self._calculate_error_rate(agent_type),
            timeout_rate=await self._calculate_timeout_rate(agent_type),
            
            # Resource metrics
            total_memory_allocated=await self._calculate_memory_usage(agent_type),
            total_cpu_allocated=await self._calculate_cpu_usage(agent_type),
            total_tokens_allocated=await self._calculate_token_usage(agent_type),
            
            # Efficiency metrics
            resource_efficiency=await self._calculate_resource_efficiency(agent_type),
            throughput_per_agent=await self._calculate_throughput_per_agent(agent_type)
        )
        
        # Store metrics
        await self.metrics_store.store(metrics)
        self.realtime_metrics[agent_type] = metrics
        
        return metrics
        
    async def _calculate_resource_efficiency(self, agent_type: AgentType) -> float:
        """Calculate how efficiently resources are being used"""
        recent_allocations = await self._get_recent_allocations(agent_type, minutes=60)
        
        if not recent_allocations:
            return 0.0
            
        total_efficiency = 0.0
        for allocation in recent_allocations:
            # Calculate efficiency as actual usage / allocated resources
            actual_usage = await self._get_actual_resource_usage(allocation)
            
            memory_efficiency = actual_usage.memory_used / allocation.memory_mb
            cpu_efficiency = actual_usage.cpu_used / allocation.cpu_cores
            token_efficiency = actual_usage.tokens_used / allocation.token_budget
            
            # Weight different resource types
            allocation_efficiency = (
                memory_efficiency * 0.4 +
                cpu_efficiency * 0.4 +
                token_efficiency * 0.2
            )
            
            total_efficiency += allocation_efficiency
            
        return total_efficiency / len(recent_allocations)

class PerformanceOptimizer:
    """Optimize pool performance based on metrics"""
    
    def __init__(self):
        self.optimization_strategies = {
            PerformanceIssue.HIGH_WAIT_TIMES: self._optimize_wait_times,
            PerformanceIssue.LOW_UTILIZATION: self._optimize_utilization,
            PerformanceIssue.RESOURCE_WASTE: self._optimize_resource_usage,
            PerformanceIssue.POOR_THROUGHPUT: self._optimize_throughput
        }
        
    async def optimize_performance(
        self, 
        agent_type: AgentType, 
        metrics: PoolMetrics
    ) -> OptimizationResult:
        """Optimize pool performance based on current metrics"""
        
        # Identify performance issues
        issues = await self._identify_performance_issues(metrics)
        
        optimizations_applied = []
        for issue in issues:
            strategy = self.optimization_strategies.get(issue.type)
            if strategy:
                result = await strategy(agent_type, issue, metrics)
                optimizations_applied.append(result)
                
        return OptimizationResult(
            agent_type=agent_type,
            issues_identified=issues,
            optimizations_applied=optimizations_applied,
            expected_improvement=await self._calculate_expected_improvement(
                optimizations_applied
            )
        )
        
    async def _optimize_wait_times(
        self, 
        agent_type: AgentType, 
        issue: PerformanceIssue,
        metrics: PoolMetrics
    ) -> OptimizationAction:
        """Optimize for reduced wait times"""
        
        if metrics.utilization > 0.8:
            # High utilization causing wait times - scale up
            recommended_increase = math.ceil(metrics.total_agents * 0.2)
            return OptimizationAction(
                type=ActionType.SCALE_UP,
                details=f"Increase pool size by {recommended_increase} to reduce wait times",
                expected_impact="Reduce wait times by ~40%",
                resource_cost=await self._calculate_scaling_cost(
                    agent_type, recommended_increase
                )
            )
        else:
            # Low utilization but still wait times - agent performance issue
            return OptimizationAction(
                type=ActionType.AGENT_TUNING,
                details="Optimize agent performance settings",
                expected_impact="Reduce wait times by ~20%"
            )
```

## Security and Isolation

### 1. Agent Security Boundaries

```python
class AgentSecurityManager:
    """Manage security boundaries for agent pools"""
    
    def __init__(self):
        self.security_profiles = {
            AgentType.DESIGN: SecurityProfile(
                allowed_tools=["read", "write_docs", "web_fetch"],
                network_access=NetworkAccess.LIMITED,
                file_access=FileAccess.READ_ONLY,
                resource_limits=ResourceLimits(memory_mb=1024, cpu_cores=1.0)
            ),
            AgentType.QA: SecurityProfile(
                allowed_tools=["read", "test_execution", "coverage_analysis"],
                network_access=NetworkAccess.TEST_ONLY,
                file_access=FileAccess.READ_WRITE_TESTS,
                resource_limits=ResourceLimits(memory_mb=2048, cpu_cores=2.0)
            ),
            AgentType.CODE: SecurityProfile(
                allowed_tools=["read", "write", "git", "test_execution"],
                network_access=NetworkAccess.LIMITED,
                file_access=FileAccess.READ_WRITE_SOURCE,
                resource_limits=ResourceLimits(memory_mb=4096, cpu_cores=2.0)
            )
        }
        
    async def enforce_security_boundaries(
        self, 
        agent: AgentInstance, 
        allocation: ResourceAllocation
    ) -> SecurityEnforcement:
        """Enforce security boundaries for agent"""
        
        profile = self.security_profiles[agent.agent_type]
        
        # Apply tool restrictions
        await agent.restrict_tools(profile.allowed_tools)
        
        # Apply network restrictions
        await agent.configure_network_access(profile.network_access)
        
        # Apply file access restrictions
        await agent.configure_file_access(profile.file_access)
        
        # Apply resource limits
        await agent.enforce_resource_limits(profile.resource_limits)
        
        # Set up monitoring
        monitor = await self._setup_security_monitoring(agent, profile)
        
        return SecurityEnforcement(
            agent_id=agent.id,
            profile=profile,
            monitor=monitor,
            enforced_at=datetime.now()
        )
```

### 2. Resource Isolation

```python
class ResourceIsolationManager:
    """Manage resource isolation between agent pools"""
    
    def __init__(self):
        self.isolation_strategies = {
            IsolationType.PROCESS: ProcessIsolation(),
            IsolationType.CONTAINER: ContainerIsolation(),
            IsolationType.VIRTUAL_MACHINE: VMIsolation()
        }
        
    async def create_isolated_environment(
        self, 
        agent_type: AgentType,
        requirements: AgentRequirements
    ) -> IsolatedEnvironment:
        """Create isolated environment for agent"""
        
        isolation_type = requirements.isolation_level
        strategy = self.isolation_strategies[isolation_type]
        
        environment = await strategy.create_environment(
            agent_type=agent_type,
            memory_limit=requirements.memory_mb,
            cpu_limit=requirements.cpu_cores,
            disk_limit=requirements.disk_space_mb,
            network_policy=requirements.network_policy
        )
        
        # Set up monitoring and cleanup
        await environment.setup_monitoring()
        await environment.setup_auto_cleanup(timeout=timedelta(hours=6))
        
        return environment
```

This comprehensive agent pool management system provides sophisticated resource allocation, dynamic scaling, intelligent load balancing, and strong security boundaries while maintaining optimal performance across parallel TDD execution cycles.