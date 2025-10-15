# Dia-TTS-Server - TODO and Technical Debt

## High Priority

### Performance & Optimization
- [ ] Profile generation pipeline to identify bottlenecks
- [ ] Optimize CUDA memory usage further (already improved from 14GB to ~7GB)
- [ ] Investigate streaming generation for real-time use cases
- [ ] Add caching for frequently used voice clones
- [ ] Review and optimize text chunking algorithm for better coherence

### Code Quality
- [ ] Add comprehensive unit tests for utils.py functions
- [ ] Add integration tests for API endpoints
- [ ] Increase test coverage to >70%
- [ ] Add automated testing in CI/CD pipeline
- [ ] Fix all linting warnings and errors

### Security
- [ ] Add rate limiting to API endpoints
- [ ] Implement input sanitization for all user inputs
- [ ] Add CORS configuration options
- [ ] Review file upload security (reference audio)
- [ ] Add authentication/authorization system (optional feature)
- [ ] Validate audio file formats more strictly

## Medium Priority

### Features
- [ ] Add support for batch processing multiple texts
- [ ] Implement queuing system for long-running jobs
- [ ] Add progress tracking API for long generations
- [ ] Support for additional audio formats (FLAC, AAC)
- [ ] Add voice mixing/interpolation capabilities
- [ ] Implement speaker diarization for multi-speaker input
- [ ] Add emotion intensity controls
- [ ] Support for SSML-like markup (extend current system)

### Code Refactoring
- [ ] Break down large functions in engine.py (generate_speech is 420+ lines)
- [ ] Extract audio post-processing into separate module
- [ ] Separate web UI logic from API logic more cleanly
- [ ] Create a proper plugin system for audio processors
- [ ] Consolidate error handling patterns
- [ ] Reduce code duplication in server.py endpoint handlers

### Documentation
- [ ] Add API usage examples for all endpoints
- [ ] Create architecture diagram
- [ ] Document voice cloning best practices
- [ ] Add troubleshooting guide for common issues
- [ ] Create developer contributing guidelines
- [ ] Add inline code documentation for complex algorithms
- [ ] Document the text chunking algorithm in detail

### Configuration
- [ ] Add validation for config.yaml on load
- [ ] Create config schema/validation using pydantic
- [ ] Add configuration migration system for version updates
- [ ] Support environment-specific configs (dev, prod)

## Low Priority

### Enhancements
- [ ] Add telemetry/metrics collection (opt-in)
- [ ] Create admin dashboard for server monitoring
- [ ] Add support for custom voice training (if feasible)
- [ ] Implement voice library/marketplace integration
- [ ] Add multilingual support (if Dia model supports it)
- [ ] Create CLI tool for batch processing
- [ ] Add webhook support for completion notifications

### Infrastructure
- [ ] Add Kubernetes deployment manifests
- [ ] Create Helm chart for easy deployment
- [ ] Add health check improvements (more detailed status)
- [ ] Implement graceful shutdown handling
- [ ] Add support for distributed deployment
- [ ] Create backup/restore utilities for voices and config

### UI Improvements
- [ ] Add waveform visualization during generation
- [ ] Implement drag-and-drop for file uploads
- [ ] Add keyboard shortcuts for common actions
- [ ] Create mobile-responsive design improvements
- [ ] Add accessibility features (WCAG compliance)
- [ ] Implement undo/redo for text editing
- [ ] Add voice preview/comparison features

## Technical Debt

### Known Issues
- [ ] Browser auto-open on server start (consider making optional)
- [ ] Whisper transcription is experimental and may be inaccurate
- [ ] Long text chunking may affect voice consistency (documented, needs improvement)
- [ ] Model state reset between chunks - investigate impact on quality
- [ ] CUDA cache clearing frequency - optimize for performance vs memory
- [ ] Some error messages could be more user-friendly

### Code Cleanup
- [ ] Remove commented-out code blocks
- [ ] Consolidate logging configuration
- [ ] Review and update all TODO/FIXME comments in code
- [ ] Remove unused imports across all modules
- [ ] Standardize exception handling patterns
- [ ] Reduce global variable usage where possible

### Dependencies
- [ ] Review and update dependency versions
- [ ] Remove unused dependencies
- [ ] Pin exact versions for reproducibility
- [ ] Create separate dev-requirements.txt
- [ ] Document why each dependency is needed

## Future Considerations

### Research & Exploration
- [ ] Explore alternative TTS models for comparison
- [ ] Investigate real-time streaming TTS
- [ ] Research voice transformation techniques
- [ ] Explore integration with LLMs for script generation
- [ ] Investigate advanced prosody controls
- [ ] Research speaker verification for cloning safety

### Scalability
- [ ] Design for horizontal scaling
- [ ] Implement load balancing strategies
- [ ] Add database support for job tracking
- [ ] Create microservices architecture option
- [ ] Design for multi-tenant deployment

## Completed ✓
- [x] Migrate to config.yaml from .env
- [x] Add BF16 model support for reduced VRAM
- [x] Implement text chunking for long inputs
- [x] Add predefined voices support
- [x] Improve voice cloning pipeline
- [x] Add seed parameter for reproducibility
- [x] Implement audio post-processing (silence trimming, etc.)
- [x] Add Whisper integration for transcript generation
- [x] Create Docker support
- [x] Add pause and speed markers support (in progress)
