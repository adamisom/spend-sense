# SpendSense - Further Work & Future Considerations

## 🔮 Post-MVP Technical Concerns

### Database & Performance
1. **SQLite Concurrency Bottlenecks** - Monitor multi-operator dashboard usage, consider PostgreSQL migration threshold
2. **Signal Schema Evolution** - Plan backward-compatible schema versioning for new behavioral signals
3. **Content Schema Changes** - Handle content catalog evolution without breaking existing persona mappings

### Business Logic Refinement  
4. **Multi-Persona Priority Conflicts** - Define behavior when users match multiple high-priority personas simultaneously
5. **Dynamic Deduplication** - Consider shorter windows for urgent recommendations (overdue payments, high utilization)
6. **Data Quality Threshold Tuning** - Validate insufficient data thresholds (≥10 transactions/30d) with real usage patterns

### Testing & Validation
7. **Extended Edge Cases** - Add extreme scenarios (cash-only users, seasonal income, gig economy patterns)
8. **Performance Benchmarks** - Define specific latency targets for recommendation generation (<500ms for 50 users)

## 📋 Planned Near-Term Work

### Draft Content Catalog ✅ 
- Create 15-20 realistic financial education items
- Map to persona triggers and behavioral signals
- Include partner offer examples with eligibility criteria

### Developer Documentation
- Streamlit operator dashboard usage guide
- API endpoint examples and testing procedures  
- Troubleshooting common development issues

---

**Document Status**: Planning - to be addressed post-Phase 3  
**Priority**: Medium - monitor during beta testing  
**Owner**: Development team

