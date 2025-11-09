## BPMN: 
Model end-to-end business process to allow a viewer of the diagram to be able to differentiate between sections of BPMN Diagrams.

- used to communicate a wide variety of information to a wide variety of stakeholders.
- BPMN able to model private/internal process with in a single pool and also applicable for public processes that describes the interaction among them.

**Private or internal: **
    - Detailed process flow for each participant.

**Public: **
    - Describes the inter-organizational cooperation.
    - Internal processes of the partners are treated as "black boxes". 
    - Specifies the information and objects that are exchanges between partners.

## BPMN Categories:
Three categories of BPMN Process are supported: 
    - Orchestration
        + Represents a process within one business entity (a single coordinating point of view). Contained in a single pool and has well-defined context. 
        + Perspective:	Single Participant
        + Control: Centralized
        + Primary Participant: One (the model owner)
        + Core Elements: Tasks, Gateways, Events
        + Main Connector: Sequence Flow
    - Collaboration
        + Shows the participants & their interactions (Pools and the message flow). It's a process that contains two or more participants as shown per pools and have message flow between them.
    - Choreography
        + Shows interactions between participants that emphasize or concentrate *message flow* rather than internal tasks. uses new  objects types (choreography task) that includes both sender & receiver within the same element. linking messages directly to these objects instead of swimlanes or separate roles.

**From what we defined, this research will focus on Private Executable (internal) Business Processes, which would be generation of an Orchestration BPMN Process that define a one business entity.
NOTE: AS for Process automation (RPA; IPA; APA), we opted for Private or Internal process modeling (Orchestration). 

## Format
JSON-based formats are generally easier for LLMs to generate, parse, and validate compared to XML
**JSON :**   
    - Natural key-value structure aligns with LLM training
    - Less verbose - fewer tokens needed
    - Clear hierarchy with arrays and objects
    - Native parsing in all modern languages
    - Type safety - arrays, objects, primitives
    - Schema validation

**XML :**   
    - More complex syntax with opening/closing tags
    - Namespace declarations add complexity
    - Mixed content can confuse LLMs
    - Complex parsers (DOM, SAX) with steeper learning curve
    - Namespace handling adds complexity
    - XSD validation is more verbose and complex

    
## Metrics & Results

- Select 20–30 representative processes (simple, medium, complex).
- Generate MAS BPMN models and have experts generate human models.
- Compare task coverage, events, gateways, GED/RGED, executable correctness.
- Record token usage and human modeling time.
- Use a form or checklist for side-by-side validation.
- Aggregate metrics and present in a table (MAS vs Human) for the paper.