import BpmnModdle from 'bpmn-moddle';
import { layoutProcess } from 'bpmn-auto-layout';
import { readFile, mkdir, writeFile, readdir } from 'node:fs/promises';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { argv } from 'node:process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const moddle = new BpmnModdle();

const MODELER_OUTPUT_DIR = path.join(__dirname, 'output', 'modeler');
const BPMN_OUTPUT_DIR = path.join(__dirname, 'output', '.bpmn');

const LAYOUT_CONFIG = {
  primary: {
    nodeSpacing: 250,
    rankSpacing: 300,
    edgeSpacing: 140,
    nodesep: 120,
    ranksep: 180,
    margin: 60,
    edgeLabelSpace: 35
  },
  fallback: {
    nodeSpacing: 350,
    rankSpacing: 400,
    edgeSpacing: 180,
    nodesep: 180,
    ranksep: 250,
    margin: 100,
    edgeLabelSpace: 50
  }
};

/**
 * Main single conversion process
 */
async function convertSingleProcess() {
  try {
    console.log('╔══════════════════════════════════════════════════════╗');
    console.log('║        BPMN JSON → XML Single Converter (v2.0)       ║');
    console.log('╚══════════════════════════════════════════════════════╝\n');

    // Get process name from command line
    const processName = argv[2];

    if (!processName) {
      console.log('Available processes:\n');
      
      const folders = await readdir(MODELER_OUTPUT_DIR);
      let index = 1;
      
      for (const folder of folders) {
        const modelPath = path.join(MODELER_OUTPUT_DIR, folder, 'bpmn_model.json');
        try {
          await readFile(modelPath);
          console.log(`  ${index}. ${folder}`);
          index++;
        } catch {
          // Skip folders without bpmn_model.json
        }
      }
      
      console.log('\nUsage:');
      console.log('  node single-converter.js "Process_Name"\n');
      console.log('Example:');
      console.log('  node single-converter.js "Vendor_Onboarding_Process"\n');
      process.exit(0);
    }

    // Ensure output directory exists
    await mkdir(BPMN_OUTPUT_DIR, { recursive: true });

    const modelPath = path.join(MODELER_OUTPUT_DIR, processName, 'bpmn_model.json');

    // Check if model exists
    try {
      await readFile(modelPath);
    } catch {
      console.log(`✗ Error: Process "${processName}" not found`);
      console.log(`\nLooking in: ${path.join(MODELER_OUTPUT_DIR, processName)}\n`);
      process.exit(1);
    }

    console.log(`[→] Converting: ${processName}\n`);
    console.log('─'.repeat(60) + '\n');

    const result = await convertSingleModel(modelPath, processName);

    // Print summary
    console.log(`✓ Successfully converted!\n`);
    console.log(`📁 Output: ${BPMN_OUTPUT_DIR}/${processName}.bpmn\n`);
    console.log('CONVERSION SUMMARY:');
    console.log('════════════════════════════════════════════════════════');
    console.log(`✓ Top-level Flow Nodes: ${result.topLevelNodes}`);
    console.log(`✓ Top-level Sequence Flows: ${result.sequenceFlows}`);
    console.log(`✓ Total Elements (including nested): ${result.totalElements}`);
    console.log(`✓ Total Top-level Elements: ${result.totalTopLevel}`);
    console.log(`✓ Error Definitions: ${result.errorDefinitions}`);
    console.log(`✓ Process: ${result.processId}`);
    console.log('════════════════════════════════════════════════════════');
    console.log('\nELEMENT TYPE BREAKDOWN:');
    Object.entries(result.elementTypeBreakdown).forEach(([type, count]) => {
      console.log(`  • ${type}: ${count}`);
    });
    console.log('\n' + '═'.repeat(60) + '\n');

  } catch (err) {
    console.error('\n[✗] Conversion failed:', err.message);
    if (err.stack) {
      console.error('Stack:', err.stack);
    }
    process.exit(1);
  }
}

/**
 * Convert a single BPMN model
 */
async function convertSingleModel(modelPath, processName) {
  const jsonStr = await readFile(modelPath, 'utf-8');
  const jsonData = JSON.parse(jsonStr);

  const processData = jsonData.rootElements[0];
  const elementRegistry = new Map();
  const flowElements = [];

  // Create error definitions
  const errorDefinitions = createErrorDefinitions(moddle, processData.flowElements, elementRegistry);

  // Process flow elements
  const processResult = processFlowElementsRecursively(
    moddle,
    processData.flowElements,
    elementRegistry
  );
  const { allElements, topLevelElements } = processResult;
  flowElements.push(...topLevelElements);

  // Create Process
  const process = moddle.create('bpmn:Process', {
    id: processData.id,
    name: processData.name,
    isExecutable: processData.isExecutable,
    flowElements: flowElements
  });

  // Create Definitions
  const definitions = moddle.create('bpmn:Definitions', {
    id: jsonData.id,
    targetNamespace: jsonData.targetNamespace,
    exporter: jsonData.exporter,
    exporterVersion: jsonData.exporterVersion,
    rootElements: [process, ...errorDefinitions]
  });

  // Convert to XML
  const { xml: initialXml } = await moddle.toXML(definitions, {
    format: true,
    preamble: true
  });

  // Apply layout
  const layoutedXml = await applyLayoutProcess(initialXml);

  // Validate and fix layout
  const validatedXml = await validateAndFixLayout(layoutedXml);

  // Save BPMN file
  const outputPath = path.join(BPMN_OUTPUT_DIR, `${processName}.bpmn`);
  await writeFile(outputPath, validatedXml);

  // Calculate statistics
  const topLevelNonSequence = topLevelElements.filter(el => el.$type !== 'bpmn:SequenceFlow').length;
  const topLevelSequence = topLevelElements.filter(el => el.$type === 'bpmn:SequenceFlow').length;

  const elementTypeBreakdown = {};
  flowElements.forEach(el => {
    const type = el.$type.replace('bpmn:', '');
    elementTypeBreakdown[type] = (elementTypeBreakdown[type] || 0) + 1;
  });

  return {
    topLevelNodes: topLevelNonSequence,
    sequenceFlows: topLevelSequence,
    totalElements: allElements.length,
    totalTopLevel: flowElements.length,
    errorDefinitions: errorDefinitions.length,
    processId: process.id,
    elementTypeBreakdown
  };
}

/**
 * Create error definitions from flow elements
 */
function createErrorDefinitions(moddle, flowElements, elementRegistry) {
  const errorDefinitions = [];
  const errorRefs = new Set();

  function findErrorRefs(elements) {
    elements.forEach(element => {
      if (element.eventDefinitions) {
        element.eventDefinitions.forEach(eventDef => {
          if (eventDef.errorRef) {
            errorRefs.add(eventDef.errorRef);
          }
        });
      }
      if (element.$type === 'bpmn:SubProcess' && element.flowElements) {
        findErrorRefs(element.flowElements);
      }
    });
  }

  findErrorRefs(flowElements);

  errorRefs.forEach(errorRef => {
    const error = moddle.create('bpmn:Error', {
      id: errorRef,
      name: errorRef
    });
    errorDefinitions.push(error);
    elementRegistry.set(errorRef, error);
  });

  return errorDefinitions;
}

/**
 * Recursively process flow elements including nested subprocesses
 */
function processFlowElementsRecursively(moddle, flowElementsData, elementRegistry, parentSubProcess = null) {
  const allElements = [];
  const topLevelElements = [];
  const nonSequenceElements = flowElementsData.filter(fe => fe.$type !== 'bpmn:SequenceFlow');
  const sequenceElements = flowElementsData.filter(fe => fe.$type === 'bpmn:SequenceFlow');

  // Create non-SequenceFlow elements
  for (const elementData of nonSequenceElements) {
    let element;

    if (elementData.$type === 'bpmn:SubProcess' && elementData.flowElements) {
      const baseProps = {
        id: elementData.id,
        name: elementData.name || undefined,
        flowElements: []
      };
      element = moddle.create('bpmn:SubProcess', baseProps);

      if (isFlowNode(element)) {
        element.incoming = [];
        element.outgoing = [];
      }
      elementRegistry.set(element.id, element);

      const nestedResult = processFlowElementsRecursively(
        moddle,
        elementData.flowElements,
        elementRegistry,
        element
      );

      element.flowElements = nestedResult.topLevelElements;
      allElements.push(...nestedResult.allElements);
    } else {
      if (elementData.$type === 'bpmn:BoundaryEvent') {
        element = createBoundaryEvent(moddle, elementData, elementRegistry);
      } else {
        element = createBpmnElement(moddle, elementData);
      }

      if (element) {
        if (isFlowNode(element)) {
          element.incoming = [];
          element.outgoing = [];
        }
        elementRegistry.set(element.id, element);
      }
    }

    if (element) {
      topLevelElements.push(element);
      allElements.push(element);
    }
  }

  // Create SequenceFlows
  for (const elementData of sequenceElements) {
    const sourceElement = elementRegistry.get(elementData.sourceRef);
    const targetElement = elementRegistry.get(elementData.targetRef);

    if (!sourceElement || !targetElement) continue;

    const sequenceFlow = moddle.create('bpmn:SequenceFlow', {
      id: elementData.id,
      name: elementData.name || undefined,
      sourceRef: sourceElement,
      targetRef: targetElement
    });

    if (isFlowNode(sourceElement) && Array.isArray(sourceElement.outgoing)) {
      sourceElement.outgoing.push(sequenceFlow);
    }
    if (isFlowNode(targetElement) && Array.isArray(targetElement.incoming)) {
      targetElement.incoming.push(sequenceFlow);
    }

    elementRegistry.set(sequenceFlow.id, sequenceFlow);
    topLevelElements.push(sequenceFlow);
    allElements.push(sequenceFlow);
  }

  return { allElements, topLevelElements };
}

/**
 * Create boundary event with all properties
 */
function createBoundaryEvent(moddle, elementData, elementRegistry) {
  const baseProps = {
    id: elementData.id,
    name: elementData.name || undefined,
    cancelActivity: elementData.cancelActivity !== undefined ? elementData.cancelActivity : true
  };

  if (elementData.attachedToRef) {
    const attachedToElement = elementRegistry.get(elementData.attachedToRef);
    if (attachedToElement) {
      baseProps.attachedToRef = attachedToElement;
    }
  }

  const boundaryEvent = moddle.create('bpmn:BoundaryEvent', baseProps);

  if (elementData.eventDefinitions && elementData.eventDefinitions.length > 0) {
    boundaryEvent.eventDefinitions = elementData.eventDefinitions.map(eventDefData => {
      let eventDef;

      if (eventDefData.$type === 'bpmn:TimerEventDefinition') {
        const timerProps = { id: `${elementData.id}_EventDef` };

        if (eventDefData.timeDuration) {
          timerProps.timeDuration = moddle.create('bpmn:FormalExpression', {
            body: eventDefData.timeDuration
          });
        }

        eventDef = moddle.create('bpmn:TimerEventDefinition', timerProps);
      } else if (eventDefData.$type === 'bpmn:ErrorEventDefinition') {
        const errorDefProps = { id: `${elementData.id}_EventDef` };

        if (eventDefData.errorRef) {
          const errorRef = elementRegistry.get(eventDefData.errorRef);
          if (errorRef) {
            errorDefProps.errorRef = errorRef;
          }
        }

        eventDef = moddle.create('bpmn:ErrorEventDefinition', errorDefProps);
      } else {
        eventDef = moddle.create(eventDefData.$type, {
          id: `${elementData.id}_EventDef`
        });
      }

      return eventDef;
    }).filter(Boolean);
  }

  return boundaryEvent;
}

/**
 * Create BPMN elements
 */
function createBpmnElement(moddle, elementData) {
  const baseProps = {
    id: elementData.id,
    name: elementData.name || undefined
  };

  try {
    switch (elementData.$type) {
      case 'bpmn:StartEvent':
        return moddle.create('bpmn:StartEvent', baseProps);
      case 'bpmn:EndEvent':
        return moddle.create('bpmn:EndEvent', baseProps);
      case 'bpmn:UserTask':
        return moddle.create('bpmn:UserTask', baseProps);
      case 'bpmn:ServiceTask':
        return moddle.create('bpmn:ServiceTask', baseProps);
      case 'bpmn:SendTask':
        return moddle.create('bpmn:SendTask', baseProps);
      case 'bpmn:ExclusiveGateway':
        return moddle.create('bpmn:ExclusiveGateway', {
          ...baseProps,
          gatewayDirection: elementData.gatewayDirection || 'Diverging'
        });
      case 'bpmn:ParallelGateway':
        return moddle.create('bpmn:ParallelGateway', {
          ...baseProps,
          gatewayDirection: elementData.gatewayDirection || 'Diverging'
        });
      case 'bpmn:BoundaryEvent':
        return moddle.create('bpmn:BoundaryEvent', baseProps);
      case 'bpmn:SubProcess':
        return moddle.create('bpmn:SubProcess', {
          ...baseProps,
          flowElements: []
        });
      case 'bpmn:Task':
        return moddle.create('bpmn:Task', baseProps);
      case 'bpmn:ManualTask':
        return moddle.create('bpmn:ManualTask', baseProps);
      case 'bpmn:BusinessRuleTask':
        return moddle.create('bpmn:BusinessRuleTask', baseProps);
      case 'bpmn:ScriptTask':
        return moddle.create('bpmn:ScriptTask', baseProps);
      case 'bpmn:CallActivity':
        return moddle.create('bpmn:CallActivity', baseProps);
      case 'bpmn:IntermediateCatchEvent':
        return moddle.create('bpmn:IntermediateCatchEvent', baseProps);
      case 'bpmn:IntermediateThrowEvent':
        return moddle.create('bpmn:IntermediateThrowEvent', baseProps);
      default:
        try {
          return moddle.create(elementData.$type, baseProps);
        } catch {
          return null;
        }
    }
  } catch {
    return null;
  }
}

/**
 * Apply auto-layout process
 */
async function applyLayoutProcess(xml) {
  try {
    const layoutedXml = await layoutProcess(xml, {
      layout: {
        nodeSpacing: LAYOUT_CONFIG.primary.nodeSpacing,
        rankSpacing: LAYOUT_CONFIG.primary.rankSpacing,
        edgeSpacing: LAYOUT_CONFIG.primary.edgeSpacing,
        orientation: 'horizontal',
        align: 'UL',
        rankdir: 'LR',
        nodesep: LAYOUT_CONFIG.primary.nodesep,
        ranksep: LAYOUT_CONFIG.primary.ranksep,
        edgeLabelSpace: LAYOUT_CONFIG.primary.edgeLabelSpace,
        marginx: LAYOUT_CONFIG.primary.margin,
        marginy: LAYOUT_CONFIG.primary.margin
      }
    });

    return layoutedXml;
  } catch (layoutError) {
    try {
      const layoutedXml = await layoutProcess(xml, {
        layout: {
          nodeSpacing: LAYOUT_CONFIG.fallback.nodeSpacing,
          rankSpacing: LAYOUT_CONFIG.fallback.rankSpacing,
          edgeSpacing: LAYOUT_CONFIG.fallback.edgeSpacing,
          orientation: 'horizontal',
          align: 'UR',
          rankdir: 'LR',
          nodesep: LAYOUT_CONFIG.fallback.nodesep,
          ranksep: LAYOUT_CONFIG.fallback.ranksep,
          edgeLabelSpace: LAYOUT_CONFIG.fallback.edgeLabelSpace,
          marginx: LAYOUT_CONFIG.fallback.margin,
          marginy: LAYOUT_CONFIG.fallback.margin
        }
      });

      return layoutedXml;
    } catch {
      return xml;
    }
  }
}

/**
 * Validate and fix layout
 */
async function validateAndFixLayout(xml) {
  try {
    const definitions = await moddle.fromXML(xml);
    let adjustmentsMade = 0;
    const diagrams = definitions.diagrams || [];

    for (const diagram of diagrams) {
      const plane = diagram.plane;
      if (!plane || !plane.planeElement) continue;

      const shapes = plane.planeElement.filter(el => el.$type === 'bpmndi:BPMNShape');
      const edges = plane.planeElement.filter(el => el.$type === 'bpmndi:BPMNEdge');

      // Fix boundary events
      const boundaryShapes = shapes.filter(s =>
        s.bpmnElement && s.bpmnElement.$type === 'bpmn:BoundaryEvent'
      );

      for (const boundaryShape of boundaryShapes) {
        if (!boundaryShape.bounds) continue;

        const boundaryElement = boundaryShape.bpmnElement;
        const attachedTo = boundaryElement.attachedToRef;

        if (!attachedTo) continue;

        const parentShape = shapes.find(s => s.bpmnElement?.id === attachedTo.id);
        if (!parentShape || !parentShape.bounds) continue;

        const parentBounds = parentShape.bounds;
        const boundaryBounds = boundaryShape.bounds;

        const newX = parentBounds.x + (parentBounds.width / 2) - (boundaryBounds.width / 2);
        const newY = parentBounds.y + parentBounds.height - (boundaryBounds.height / 2);

        if (Math.abs(boundaryBounds.x - newX) > 5 || Math.abs(boundaryBounds.y - newY) > 5) {
          boundaryBounds.x = newX;
          boundaryBounds.y = newY;
          adjustmentsMade++;
        }
      }

      // Fix overlapping shapes
      const SHAPE_BUFFER = 30;

      for (let i = 0; i < shapes.length; i++) {
        for (let j = i + 1; j < shapes.length; j++) {
          const shape1 = shapes[i];
          const shape2 = shapes[j];

          if (!shape1.bounds || !shape2.bounds) continue;

          if (shape1.bpmnElement?.$type === 'bpmn:BoundaryEvent' &&
            shape1.bpmnElement.attachedToRef?.id === shape2.bpmnElement?.id) continue;
          if (shape2.bpmnElement?.$type === 'bpmn:BoundaryEvent' &&
            shape2.bpmnElement.attachedToRef?.id === shape1.bpmnElement?.id) continue;

          const b1 = shape1.bounds;
          const b2 = shape2.bounds;

          const overlapX = !(b1.x + b1.width + SHAPE_BUFFER < b2.x ||
            b2.x + b2.width + SHAPE_BUFFER < b1.x);
          const overlapY = !(b1.y + b1.height + SHAPE_BUFFER < b2.y ||
            b2.y + b2.height + SHAPE_BUFFER < b1.y);

          if (overlapX && overlapY) {
            const centerX1 = b1.x + b1.width / 2;
            const centerX2 = b2.x + b2.width / 2;
            const centerY1 = b1.y + b1.height / 2;
            const centerY2 = b2.y + b2.height / 2;

            const deltaX = Math.abs(centerX2 - centerX1);
            const deltaY = Math.abs(centerY2 - centerY1);

            if (deltaX > deltaY) {
              if (centerX2 > centerX1) {
                b2.x = b1.x + b1.width + SHAPE_BUFFER;
              } else {
                b2.x = b1.x - b2.width - SHAPE_BUFFER;
              }
            } else {
              if (centerY2 > centerY1) {
                b2.y = b1.y + b1.height + SHAPE_BUFFER;
              } else {
                b2.y = b1.y - b2.height - SHAPE_BUFFER;
              }
            }

            adjustmentsMade++;
          }
        }
      }
    }

    if (adjustmentsMade > 0) {
      const { xml: fixedXml } = await moddle.toXML(definitions, {
        format: true,
        preamble: true
      });
      return fixedXml;
    }

    return xml;
  } catch {
    return xml;
  }
}

/**
 * Check if element is a FlowNode
 */
function isFlowNode(element) {
  const flowNodeTypes = [
    'bpmn:FlowNode',
    'bpmn:Task', 'bpmn:UserTask', 'bpmn:ServiceTask', 'bpmn:SendTask', 'bpmn:ReceiveTask',
    'bpmn:ManualTask', 'bpmn:BusinessRuleTask', 'bpmn:ScriptTask',
    'bpmn:StartEvent', 'bpmn:EndEvent', 'bpmn:IntermediateCatchEvent', 'bpmn:IntermediateThrowEvent',
    'bpmn:BoundaryEvent',
    'bpmn:ExclusiveGateway', 'bpmn:ParallelGateway', 'bpmn:InclusiveGateway',
    'bpmn:EventBasedGateway', 'bpmn:ComplexGateway',
    'bpmn:CallActivity', 'bpmn:SubProcess'
  ];
  return flowNodeTypes.some(type => element.$type === type);
}

// Run the single conversion
convertSingleProcess();