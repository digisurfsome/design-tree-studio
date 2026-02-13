// State
const state = {
  tool: 'select', // select, move, arrow, rect, text, floatText
  color: '#ef4444',
  lineWidth: 4,
  chunks: [],
  floatingTexts: [],
  annotations: [],
  moodBoardImages: [],
  history: [],
  isDrawing: false,
  startX: 0,
  startY: 0,
  currentX: 0,
  currentY: 0,
  draggedChunk: null,
  draggedFloatText: null,
  dragOffsetX: 0,
  dragOffsetY: 0,
  baseImage: null,
  canvasOffsetX: 0,
  canvasOffsetY: 0,
  smartFillEnabled: true,
  geminiApiKey: '',
  // New features
  snapToGrid: true,
  gridSize: 16,
  zoom: 1,
  selectedChunks: [], // For multi-select
  isResizing: false,
  resizeHandle: null,
  resizeChunk: null
};

// DOM Elements
const canvas = document.getElementById('mainCanvas');
const ctx = canvas.getContext('2d');
const canvasContainer = document.getElementById('canvasContainer');
const chunksLayer = document.getElementById('chunksLayer');
const floatingTextsLayer = document.getElementById('floatingTextsLayer');
const selectionBox = document.getElementById('selectionBox');
const statusText = document.getElementById('statusText');
const chunkCount = document.getElementById('chunkCount');
const floatCount = document.getElementById('floatCount');

// Initialize
async function init() {
  // Load screenshot from storage
  const data = await chrome.storage.local.get(['screenshot', 'geminiApiKey']);
  if (data.screenshot) {
    loadImage(data.screenshot);
  } else {
    statusText.textContent = 'No screenshot found - capture a page first';
  }

  // Load saved API key
  if (data.geminiApiKey) {
    state.geminiApiKey = data.geminiApiKey;
    document.getElementById('geminiApiKey').value = data.geminiApiKey;
  }

  setupEventListeners();

  // Show instructions on first use
  const hasSeenInstructions = localStorage.getItem('mockup-instructions-seen-v3');
  if (!hasSeenInstructions) {
    document.getElementById('instructionsModal').classList.remove('hidden');
  } else {
    document.getElementById('instructionsModal').classList.add('hidden');
  }
}

function loadImage(dataUrl) {
  const img = new Image();
  img.onload = () => {
    state.baseImage = img;
    canvas.width = img.width;
    canvas.height = img.height;
    render();
    updateCanvasOffset();
    statusText.textContent = 'Ready - Draw a rectangle to select a chunk';
  };
  img.src = dataUrl;
}

function updateCanvasOffset() {
  const rect = canvas.getBoundingClientRect();
  state.canvasOffsetX = rect.left;
  state.canvasOffsetY = rect.top;
}

// Event Listeners
function setupEventListeners() {
  // Tool buttons
  document.getElementById('selectTool').addEventListener('click', () => setTool('select'));
  document.getElementById('moveTool').addEventListener('click', () => setTool('move'));
  document.getElementById('arrowTool').addEventListener('click', () => setTool('arrow'));
  document.getElementById('rectTool').addEventListener('click', () => setTool('rect'));
  document.getElementById('textTool').addEventListener('click', () => setTool('text'));
  document.getElementById('floatTextTool').addEventListener('click', () => setTool('floatText'));

  // Color buttons
  document.querySelectorAll('.color-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.color = btn.dataset.color;
    });
  });

  // Line width
  document.getElementById('lineWidth').addEventListener('change', (e) => {
    state.lineWidth = parseInt(e.target.value);
  });

  // Smart fill toggle
  document.getElementById('smartFill').addEventListener('change', (e) => {
    state.smartFillEnabled = e.target.checked;
  });

  // Snap to grid toggle
  document.getElementById('snapGrid').addEventListener('change', (e) => {
    state.snapToGrid = e.target.checked;
  });

  // Grid size
  document.getElementById('gridSize').addEventListener('change', (e) => {
    state.gridSize = parseInt(e.target.value);
  });

  // Zoom controls
  document.getElementById('zoomIn').addEventListener('click', () => zoomCanvas(0.1));
  document.getElementById('zoomOut').addEventListener('click', () => zoomCanvas(-0.1));
  document.getElementById('zoomReset').addEventListener('click', () => {
    state.zoom = 1;
    applyZoom();
  });

  // Action buttons
  document.getElementById('undoBtn').addEventListener('click', undo);
  document.getElementById('clearChunks').addEventListener('click', clearAll);
  document.getElementById('duplicateBtn').addEventListener('click', duplicateSelected);
  document.getElementById('exportBtn').addEventListener('click', exportImage);

  // AI Panel
  document.getElementById('aiSuggestBtn').addEventListener('click', () => togglePanel('ai'));
  document.getElementById('closeSidePanel').addEventListener('click', () => closePanel());
  document.getElementById('generateSuggestions').addEventListener('click', generateAISuggestions);
  document.getElementById('geminiApiKey').addEventListener('change', saveApiKey);

  // Mood Board Panel
  document.getElementById('moodBoardBtn').addEventListener('click', () => togglePanel('mood'));
  document.getElementById('closeMoodBoard').addEventListener('click', () => closePanel());
  document.getElementById('uploadMoodBtn').addEventListener('click', () => {
    document.getElementById('moodBoardInput').click();
  });
  document.getElementById('moodBoardInput').addEventListener('change', handleMoodBoardUpload);

  // Modal
  document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('instructionsModal').classList.add('hidden');
    localStorage.setItem('mockup-instructions-seen-v3', 'true');
  });

  // Text input
  document.getElementById('textSubmit').addEventListener('click', submitText);
  document.getElementById('textInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') submitText();
  });

  // Canvas events
  canvas.addEventListener('mousedown', handleMouseDown);
  canvas.addEventListener('mousemove', handleMouseMove);
  canvas.addEventListener('mouseup', handleMouseUp);
  canvas.addEventListener('mouseleave', handleMouseUp);

  // Mouse wheel zoom
  canvasContainer.addEventListener('wheel', (e) => {
    if (e.ctrlKey) {
      e.preventDefault();
      zoomCanvas(e.deltaY > 0 ? -0.1 : 0.1);
    }
  }, { passive: false });

  // Window resize
  window.addEventListener('resize', updateCanvasOffset);
  window.addEventListener('scroll', updateCanvasOffset);

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    switch(e.key.toLowerCase()) {
      case 'v': setTool('select'); break;
      case 'm': setTool('move'); break;
      case 'a': setTool('arrow'); break;
      case 'r': setTool('rect'); break;
      case 't': setTool('text'); break;
      case 'f': setTool('floatText'); break;
      case 'g': toggleSnapGrid(); break;
      case 'd':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          duplicateSelected();
        }
        break;
      case 'z':
        if (e.ctrlKey || e.metaKey) undo();
        break;
      case '=':
      case '+':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          zoomCanvas(0.1);
        }
        break;
      case '-':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          zoomCanvas(-0.1);
        }
        break;
      case '0':
        if (e.ctrlKey || e.metaKey) {
          e.preventDefault();
          state.zoom = 1;
          applyZoom();
        }
        break;
      case 'escape':
        cancelAction();
        clearSelection();
        break;
    }
  });

  // Click outside chunks to deselect
  canvas.addEventListener('click', (e) => {
    if (!e.shiftKey) {
      clearSelection();
    }
  });
}

function setTool(tool) {
  state.tool = tool;
  document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
  const toolBtn = document.getElementById(tool + 'Tool') || document.getElementById(tool + 'TextTool');
  toolBtn?.classList.add('active');

  // Update cursor
  canvas.style.cursor = tool === 'move' ? 'grab' : 'crosshair';

  // Update status
  const statusMessages = {
    select: 'Draw rectangle to cut chunk | Shift+click to multi-select',
    move: 'Drag chunks to move | Shift+click to multi-select',
    arrow: 'Click and drag to draw an arrow',
    rect: 'Click and drag to draw a rectangle',
    text: 'Click to place text on canvas',
    floatText: 'Click to place a movable floating label'
  };
  statusText.textContent = statusMessages[tool] || 'Ready';

  // Hide text input if switching away
  if (tool !== 'text' && tool !== 'floatText') {
    document.getElementById('textInputContainer').classList.add('hidden');
  }
}

function toggleSnapGrid() {
  state.snapToGrid = !state.snapToGrid;
  document.getElementById('snapGrid').checked = state.snapToGrid;
  statusText.textContent = `Snap to grid: ${state.snapToGrid ? 'ON' : 'OFF'}`;
}

// Zoom functions
function zoomCanvas(delta) {
  state.zoom = Math.max(0.25, Math.min(3, state.zoom + delta));
  applyZoom();
}

function applyZoom() {
  canvas.style.transform = `scale(${state.zoom})`;
  canvas.style.transformOrigin = 'center center';
  document.getElementById('zoomLevel').textContent = `${Math.round(state.zoom * 100)}%`;
  updateCanvasOffset();
  rebuildChunks();
  rebuildFloatingTexts();
}

// Snap to grid helper
function snapToGrid(value) {
  if (!state.snapToGrid) return value;
  return Math.round(value / state.gridSize) * state.gridSize;
}

function getMousePos(e) {
  updateCanvasOffset();
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  };
}

function handleMouseDown(e) {
  const pos = getMousePos(e);
  state.isDrawing = true;
  state.startX = pos.x;
  state.startY = pos.y;

  if (state.tool === 'text' || state.tool === 'floatText') {
    showTextInput(e.clientX, e.clientY, pos.x, pos.y);
    state.isDrawing = false;
  }
}

function handleMouseMove(e) {
  if (!state.isDrawing) return;

  const pos = getMousePos(e);
  state.currentX = pos.x;
  state.currentY = pos.y;

  if (state.tool === 'select') {
    // Show selection box - position relative to canvas container
    const canvasRect = canvas.getBoundingClientRect();
    const containerRect = canvasContainer.getBoundingClientRect();
    const scaleX = canvasRect.width / canvas.width;
    const scaleY = canvasRect.height / canvas.height;

    // Calculate position relative to container (accounting for scroll)
    const canvasOffsetX = canvasRect.left - containerRect.left + canvasContainer.scrollLeft;
    const canvasOffsetY = canvasRect.top - containerRect.top + canvasContainer.scrollTop;

    const left = Math.min(state.startX, state.currentX) * scaleX + canvasOffsetX;
    const top = Math.min(state.startY, state.currentY) * scaleY + canvasOffsetY;
    const width = Math.abs(state.currentX - state.startX) * scaleX;
    const height = Math.abs(state.currentY - state.startY) * scaleY;

    selectionBox.style.display = 'block';
    selectionBox.style.left = left + 'px';
    selectionBox.style.top = top + 'px';
    selectionBox.style.width = width + 'px';
    selectionBox.style.height = height + 'px';
  } else if (state.tool === 'arrow' || state.tool === 'rect') {
    // Live preview
    render();
    drawAnnotationPreview();
  }
}

function handleMouseUp(e) {
  if (!state.isDrawing) return;
  state.isDrawing = false;

  const pos = getMousePos(e);
  state.currentX = pos.x;
  state.currentY = pos.y;

  selectionBox.style.display = 'none';

  if (state.tool === 'select') {
    createChunk();
  } else if (state.tool === 'arrow' || state.tool === 'rect') {
    createAnnotation();
  }
}

// Smart Fill: Sample average background color from edges of selection
function sampleBackgroundColor(x, y, width, height) {
  if (!state.baseImage) return '#000000';

  // Create a temporary canvas to sample the image
  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = state.baseImage.width;
  tempCanvas.height = state.baseImage.height;
  const tempCtx = tempCanvas.getContext('2d');
  tempCtx.drawImage(state.baseImage, 0, 0);

  // Sample pixels from the edges of the selection
  const sampleSize = 5;
  const samples = [];

  // Top edge
  for (let i = 0; i < width; i += Math.max(1, Math.floor(width / sampleSize))) {
    if (y > 0) {
      const pixel = tempCtx.getImageData(Math.floor(x + i), Math.floor(y - 1), 1, 1).data;
      samples.push([pixel[0], pixel[1], pixel[2]]);
    }
  }

  // Bottom edge
  for (let i = 0; i < width; i += Math.max(1, Math.floor(width / sampleSize))) {
    if (y + height < tempCanvas.height) {
      const pixel = tempCtx.getImageData(Math.floor(x + i), Math.floor(y + height), 1, 1).data;
      samples.push([pixel[0], pixel[1], pixel[2]]);
    }
  }

  // Left edge
  for (let i = 0; i < height; i += Math.max(1, Math.floor(height / sampleSize))) {
    if (x > 0) {
      const pixel = tempCtx.getImageData(Math.floor(x - 1), Math.floor(y + i), 1, 1).data;
      samples.push([pixel[0], pixel[1], pixel[2]]);
    }
  }

  // Right edge
  for (let i = 0; i < height; i += Math.max(1, Math.floor(height / sampleSize))) {
    if (x + width < tempCanvas.width) {
      const pixel = tempCtx.getImageData(Math.floor(x + width), Math.floor(y + i), 1, 1).data;
      samples.push([pixel[0], pixel[1], pixel[2]]);
    }
  }

  if (samples.length === 0) return '#000000';

  // Calculate average color
  const avg = samples.reduce((acc, [r, g, b]) => {
    return [acc[0] + r, acc[1] + g, acc[2] + b];
  }, [0, 0, 0]).map(v => Math.round(v / samples.length));

  return `rgb(${avg[0]}, ${avg[1]}, ${avg[2]})`;
}

function createChunk() {
  const x = Math.min(state.startX, state.currentX);
  const y = Math.min(state.startY, state.currentY);
  const width = Math.abs(state.currentX - state.startX);
  const height = Math.abs(state.currentY - state.startY);

  if (width < 10 || height < 10) return; // Too small

  // Sample background color if smart fill is enabled
  const bgColor = state.smartFillEnabled ? sampleBackgroundColor(x, y, width, height) : 'rgba(0, 0, 0, 0.3)';

  // Create image data for the chunk
  const chunkCanvas = document.createElement('canvas');
  chunkCanvas.width = width;
  chunkCanvas.height = height;
  const chunkCtx = chunkCanvas.getContext('2d');
  chunkCtx.drawImage(state.baseImage, x, y, width, height, 0, 0, width, height);

  const chunk = {
    id: 'chunk-' + Date.now(),
    originalX: x,
    originalY: y,
    x: x,
    y: y,
    width: width,
    height: height,
    imageData: chunkCanvas.toDataURL(),
    backgroundColor: bgColor,
    selected: false
  };

  state.chunks.push(chunk);
  saveHistory();
  createChunkElement(chunk);
  updateChunkCount();
  render();
}

function createChunkElement(chunk) {
  const canvasRect = canvas.getBoundingClientRect();
  const containerRect = canvasContainer.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  // Calculate canvas offset relative to container (accounting for scroll)
  const canvasOffsetX = canvasRect.left - containerRect.left + canvasContainer.scrollLeft;
  const canvasOffsetY = canvasRect.top - containerRect.top + canvasContainer.scrollTop;

  const div = document.createElement('div');
  div.className = 'chunk' + (chunk.selected ? ' selected' : '');
  div.id = chunk.id;
  div.style.left = (chunk.x * scaleX + canvasOffsetX) + 'px';
  div.style.top = (chunk.y * scaleY + canvasOffsetY) + 'px';
  div.style.width = (chunk.width * scaleX) + 'px';
  div.style.height = (chunk.height * scaleY) + 'px';

  const img = document.createElement('img');
  img.src = chunk.imageData;
  img.style.width = '100%';
  img.style.height = '100%';
  img.draggable = false;
  div.appendChild(img);

  // Delete button
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'chunk-delete';
  deleteBtn.innerHTML = '×';
  deleteBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    deleteChunk(chunk.id);
  });
  div.appendChild(deleteBtn);

  // Duplicate button
  const dupBtn = document.createElement('button');
  dupBtn.className = 'chunk-duplicate';
  dupBtn.innerHTML = '⧉';
  dupBtn.title = 'Duplicate (Ctrl+D)';
  dupBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    duplicateChunk(chunk.id);
  });
  div.appendChild(dupBtn);

  // Resize handles
  const handles = ['nw', 'ne', 'sw', 'se'];
  handles.forEach(pos => {
    const handle = document.createElement('div');
    handle.className = `resize-handle resize-${pos}`;
    handle.dataset.handle = pos;
    handle.addEventListener('mousedown', (e) => startResize(e, chunk, pos));
    div.appendChild(handle);
  });

  // Click to select (with shift for multi-select)
  div.addEventListener('click', (e) => {
    e.stopPropagation();
    if (e.shiftKey) {
      toggleChunkSelection(chunk.id);
    } else {
      selectChunk(chunk.id);
    }
  });

  // Drag events
  div.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('resize-handle')) return;
    startDragChunk(e, chunk);
  });

  chunksLayer.appendChild(div);
}

// Selection functions
function selectChunk(id) {
  clearSelection();
  const chunk = state.chunks.find(c => c.id === id);
  if (chunk) {
    chunk.selected = true;
    state.selectedChunks = [id];
    updateChunkVisuals();
  }
}

function toggleChunkSelection(id) {
  const chunk = state.chunks.find(c => c.id === id);
  if (chunk) {
    chunk.selected = !chunk.selected;
    if (chunk.selected) {
      state.selectedChunks.push(id);
    } else {
      state.selectedChunks = state.selectedChunks.filter(cid => cid !== id);
    }
    updateChunkVisuals();
  }
}

function clearSelection() {
  state.chunks.forEach(c => c.selected = false);
  state.selectedChunks = [];
  updateChunkVisuals();
}

function updateChunkVisuals() {
  state.chunks.forEach(chunk => {
    const div = document.getElementById(chunk.id);
    if (div) {
      if (chunk.selected) {
        div.classList.add('selected');
      } else {
        div.classList.remove('selected');
      }
    }
  });
}

// Resize functions
function startResize(e, chunk, handle) {
  e.preventDefault();
  e.stopPropagation();

  state.isResizing = true;
  state.resizeHandle = handle;
  state.resizeChunk = chunk;
  state.startX = e.clientX;
  state.startY = e.clientY;

  const moveHandler = (e) => doResize(e);
  const upHandler = () => {
    document.removeEventListener('mousemove', moveHandler);
    document.removeEventListener('mouseup', upHandler);
    endResize();
  };

  document.addEventListener('mousemove', moveHandler);
  document.addEventListener('mouseup', upHandler);
}

function doResize(e) {
  if (!state.isResizing || !state.resizeChunk) return;

  const canvasRect = canvas.getBoundingClientRect();
  const containerRect = canvasContainer.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  // Calculate canvas offset relative to container (accounting for scroll)
  const canvasOffsetX = canvasRect.left - containerRect.left + canvasContainer.scrollLeft;
  const canvasOffsetY = canvasRect.top - containerRect.top + canvasContainer.scrollTop;

  const deltaX = (e.clientX - state.startX) / scaleX;
  const deltaY = (e.clientY - state.startY) / scaleY;

  const chunk = state.resizeChunk;
  const handle = state.resizeHandle;

  let newX = chunk.x;
  let newY = chunk.y;
  let newWidth = chunk.width;
  let newHeight = chunk.height;

  if (handle.includes('w')) {
    newX = chunk.x + deltaX;
    newWidth = chunk.width - deltaX;
  }
  if (handle.includes('e')) {
    newWidth = chunk.width + deltaX;
  }
  if (handle.includes('n')) {
    newY = chunk.y + deltaY;
    newHeight = chunk.height - deltaY;
  }
  if (handle.includes('s')) {
    newHeight = chunk.height + deltaY;
  }

  // Minimum size
  if (newWidth < 20) newWidth = 20;
  if (newHeight < 20) newHeight = 20;

  // Apply snap
  newX = snapToGrid(newX);
  newY = snapToGrid(newY);
  newWidth = snapToGrid(newWidth);
  newHeight = snapToGrid(newHeight);

  // Update chunk visually
  const div = document.getElementById(chunk.id);
  div.style.left = (newX * scaleX + canvasOffsetX) + 'px';
  div.style.top = (newY * scaleY + canvasOffsetY) + 'px';
  div.style.width = (newWidth * scaleX) + 'px';
  div.style.height = (newHeight * scaleY) + 'px';

  state.startX = e.clientX;
  state.startY = e.clientY;
  chunk.x = newX;
  chunk.y = newY;
  chunk.width = newWidth;
  chunk.height = newHeight;

  render();
}

function endResize() {
  if (state.isResizing) {
    saveHistory();
  }
  state.isResizing = false;
  state.resizeHandle = null;
  state.resizeChunk = null;
}

// Duplicate functions
function duplicateSelected() {
  if (state.selectedChunks.length === 0) {
    statusText.textContent = 'Select a chunk first (click on it)';
    return;
  }

  state.selectedChunks.forEach(id => duplicateChunk(id));
}

function duplicateChunk(id) {
  const original = state.chunks.find(c => c.id === id);
  if (!original) return;

  const newChunk = {
    ...original,
    id: 'chunk-' + Date.now() + Math.random(),
    x: original.x + 20,
    y: original.y + 20,
    selected: false
  };

  state.chunks.push(newChunk);
  createChunkElement(newChunk);
  saveHistory();
  updateChunkCount();
  render();

  statusText.textContent = 'Chunk duplicated!';
}

function startDragChunk(e, chunk) {
  if (state.tool !== 'select' && state.tool !== 'move') return;
  if (state.isResizing) return;

  e.preventDefault();

  // If not already selected, select this chunk
  if (!chunk.selected) {
    if (!e.shiftKey) {
      clearSelection();
    }
    chunk.selected = true;
    state.selectedChunks.push(chunk.id);
    updateChunkVisuals();
  }

  const div = document.getElementById(chunk.id);
  div.classList.add('dragging');

  const canvasRect = canvas.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  state.draggedChunk = chunk;
  state.dragOffsetX = e.clientX - (chunk.x * scaleX + canvasRect.left);
  state.dragOffsetY = e.clientY - (chunk.y * scaleY + canvasRect.top);

  // Store initial positions for all selected chunks
  state.selectedChunks.forEach(id => {
    const c = state.chunks.find(ch => ch.id === id);
    if (c) {
      c._dragStartX = c.x;
      c._dragStartY = c.y;
    }
  });

  const moveHandler = (e) => dragChunk(e);
  const upHandler = () => {
    document.removeEventListener('mousemove', moveHandler);
    document.removeEventListener('mouseup', upHandler);
    endDragChunk();
  };

  document.addEventListener('mousemove', moveHandler);
  document.addEventListener('mouseup', upHandler);
}

function dragChunk(e) {
  if (!state.draggedChunk) return;

  const canvasRect = canvas.getBoundingClientRect();
  const containerRect = canvasContainer.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  // Calculate canvas offset relative to container (accounting for scroll)
  const canvasOffsetX = canvasRect.left - containerRect.left + canvasContainer.scrollLeft;
  const canvasOffsetY = canvasRect.top - containerRect.top + canvasContainer.scrollTop;

  let newX = (e.clientX - state.dragOffsetX - canvasRect.left) / scaleX;
  let newY = (e.clientY - state.dragOffsetY - canvasRect.top) / scaleY;

  // Apply snap to grid
  newX = snapToGrid(newX);
  newY = snapToGrid(newY);

  const deltaX = newX - state.draggedChunk._dragStartX;
  const deltaY = newY - state.draggedChunk._dragStartY;

  // Move all selected chunks
  state.selectedChunks.forEach(id => {
    const chunk = state.chunks.find(c => c.id === id);
    if (chunk) {
      chunk.x = snapToGrid(chunk._dragStartX + deltaX);
      chunk.y = snapToGrid(chunk._dragStartY + deltaY);

      const div = document.getElementById(chunk.id);
      div.style.left = (chunk.x * scaleX + canvasOffsetX) + 'px';
      div.style.top = (chunk.y * scaleY + canvasOffsetY) + 'px';
    }
  });

  render();
}

function endDragChunk() {
  if (state.draggedChunk) {
    state.selectedChunks.forEach(id => {
      const div = document.getElementById(id);
      if (div) div.classList.remove('dragging');
      const chunk = state.chunks.find(c => c.id === id);
      if (chunk) {
        delete chunk._dragStartX;
        delete chunk._dragStartY;
      }
    });
    saveHistory();
  }
  state.draggedChunk = null;
}

function deleteChunk(id) {
  state.chunks = state.chunks.filter(c => c.id !== id);
  state.selectedChunks = state.selectedChunks.filter(cid => cid !== id);
  const div = document.getElementById(id);
  if (div) div.remove();
  saveHistory();
  updateChunkCount();
  render();
}

// Floating Text Functions
function createFloatingText(text, canvasX, canvasY) {
  const floatText = {
    id: 'float-' + Date.now(),
    text: text,
    x: canvasX,
    y: canvasY,
    color: state.color
  };

  state.floatingTexts.push(floatText);
  saveHistory();
  createFloatingTextElement(floatText);
  updateFloatCount();
}

function createFloatingTextElement(floatText) {
  const canvasRect = canvas.getBoundingClientRect();
  const containerRect = canvasContainer.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  // Calculate canvas offset relative to container (accounting for scroll)
  const canvasOffsetX = canvasRect.left - containerRect.left + canvasContainer.scrollLeft;
  const canvasOffsetY = canvasRect.top - containerRect.top + canvasContainer.scrollTop;

  const div = document.createElement('div');
  div.className = 'floating-text';
  div.id = floatText.id;
  div.textContent = floatText.text;
  div.style.left = (floatText.x * scaleX + canvasOffsetX) + 'px';
  div.style.top = (floatText.y * scaleY + canvasOffsetY) + 'px';
  div.style.borderColor = floatText.color;
  div.style.color = floatText.color;

  // Delete button
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'floating-text-delete';
  deleteBtn.innerHTML = '×';
  deleteBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    deleteFloatingText(floatText.id);
  });
  div.appendChild(deleteBtn);

  // Drag events
  div.addEventListener('mousedown', (e) => startDragFloatText(e, floatText));

  floatingTextsLayer.appendChild(div);
}

function startDragFloatText(e, floatText) {
  e.preventDefault();
  const div = document.getElementById(floatText.id);
  div.classList.add('dragging');

  const canvasRect = canvas.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  state.draggedFloatText = floatText;
  state.dragOffsetX = e.clientX - (floatText.x * scaleX + canvasRect.left);
  state.dragOffsetY = e.clientY - (floatText.y * scaleY + canvasRect.top);

  const moveHandler = (e) => dragFloatText(e);
  const upHandler = () => {
    document.removeEventListener('mousemove', moveHandler);
    document.removeEventListener('mouseup', upHandler);
    endDragFloatText();
  };

  document.addEventListener('mousemove', moveHandler);
  document.addEventListener('mouseup', upHandler);
}

function dragFloatText(e) {
  if (!state.draggedFloatText) return;

  const canvasRect = canvas.getBoundingClientRect();
  const containerRect = canvasContainer.getBoundingClientRect();
  const scaleX = canvasRect.width / canvas.width;
  const scaleY = canvasRect.height / canvas.height;

  // Calculate canvas offset relative to container (accounting for scroll)
  const canvasOffsetX = canvasRect.left - containerRect.left + canvasContainer.scrollLeft;
  const canvasOffsetY = canvasRect.top - containerRect.top + canvasContainer.scrollTop;

  let newX = (e.clientX - state.dragOffsetX - canvasRect.left) / scaleX;
  let newY = (e.clientY - state.dragOffsetY - canvasRect.top) / scaleY;

  // Apply snap
  newX = snapToGrid(newX);
  newY = snapToGrid(newY);

  state.draggedFloatText.x = newX;
  state.draggedFloatText.y = newY;

  const div = document.getElementById(state.draggedFloatText.id);
  div.style.left = (newX * scaleX + canvasOffsetX) + 'px';
  div.style.top = (newY * scaleY + canvasOffsetY) + 'px';
}

function endDragFloatText() {
  if (state.draggedFloatText) {
    const div = document.getElementById(state.draggedFloatText.id);
    div.classList.remove('dragging');
    saveHistory();
  }
  state.draggedFloatText = null;
}

function deleteFloatingText(id) {
  state.floatingTexts = state.floatingTexts.filter(f => f.id !== id);
  const div = document.getElementById(id);
  if (div) div.remove();
  saveHistory();
  updateFloatCount();
}

function updateFloatCount() {
  floatCount.textContent = `Labels: ${state.floatingTexts.length}`;
}

function createAnnotation() {
  const annotation = {
    type: state.tool,
    startX: state.startX,
    startY: state.startY,
    endX: state.currentX,
    endY: state.currentY,
    color: state.color,
    lineWidth: state.lineWidth
  };

  if (Math.abs(annotation.endX - annotation.startX) < 5 &&
      Math.abs(annotation.endY - annotation.startY) < 5) return;

  state.annotations.push(annotation);
  saveHistory();
  render();
}

function drawAnnotationPreview() {
  if (state.tool === 'arrow') {
    drawArrow(ctx, state.startX, state.startY, state.currentX, state.currentY, state.color, state.lineWidth);
  } else if (state.tool === 'rect') {
    drawRect(ctx, state.startX, state.startY, state.currentX, state.currentY, state.color, state.lineWidth);
  }
}

function drawArrow(ctx, fromX, fromY, toX, toY, color, lineWidth) {
  const headLength = 15 + lineWidth * 2;
  const angle = Math.atan2(toY - fromY, toX - fromX);

  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = 'round';

  // Line
  ctx.beginPath();
  ctx.moveTo(fromX, fromY);
  ctx.lineTo(toX, toY);
  ctx.stroke();

  // Arrowhead
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), toY - headLength * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), toY - headLength * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
}

function drawRect(ctx, x1, y1, x2, y2, color, lineWidth) {
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.strokeRect(
    Math.min(x1, x2),
    Math.min(y1, y2),
    Math.abs(x2 - x1),
    Math.abs(y2 - y1)
  );
}

function showTextInput(clientX, clientY, canvasX, canvasY) {
  const container = document.getElementById('textInputContainer');
  container.classList.remove('hidden');
  container.style.left = clientX + 'px';
  container.style.top = clientY + 'px';
  container.dataset.canvasX = canvasX;
  container.dataset.canvasY = canvasY;
  document.getElementById('textInput').focus();
}

function submitText() {
  const container = document.getElementById('textInputContainer');
  const input = document.getElementById('textInput');
  const text = input.value.trim();

  if (text) {
    const canvasX = parseFloat(container.dataset.canvasX);
    const canvasY = parseFloat(container.dataset.canvasY);

    if (state.tool === 'floatText') {
      // Create floating text overlay
      createFloatingText(text, canvasX, canvasY);
    } else {
      // Create canvas annotation text
      const annotation = {
        type: 'text',
        x: canvasX,
        y: canvasY,
        text: text,
        color: state.color,
        fontSize: 16 + state.lineWidth * 4
      };
      state.annotations.push(annotation);
      saveHistory();
      render();
    }
  }

  input.value = '';
  container.classList.add('hidden');
}

function render() {
  if (!state.baseImage) return;

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw base image
  ctx.drawImage(state.baseImage, 0, 0);

  // Draw filled areas where chunks were cut (smart fill or dark overlay)
  state.chunks.forEach(chunk => {
    ctx.fillStyle = chunk.backgroundColor || 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(chunk.originalX, chunk.originalY, chunk.width, chunk.height);
  });

  // Draw annotations
  state.annotations.forEach(ann => {
    if (ann.type === 'arrow') {
      drawArrow(ctx, ann.startX, ann.startY, ann.endX, ann.endY, ann.color, ann.lineWidth);
    } else if (ann.type === 'rect') {
      drawRect(ctx, ann.startX, ann.startY, ann.endX, ann.endY, ann.color, ann.lineWidth);
    } else if (ann.type === 'text') {
      ctx.font = `bold ${ann.fontSize}px -apple-system, sans-serif`;
      ctx.fillStyle = ann.color;
      ctx.fillText(ann.text, ann.x, ann.y);
    }
  });
}

function saveHistory() {
  state.history.push({
    chunks: JSON.parse(JSON.stringify(state.chunks)),
    floatingTexts: JSON.parse(JSON.stringify(state.floatingTexts)),
    annotations: JSON.parse(JSON.stringify(state.annotations))
  });
  // Keep only last 20 states
  if (state.history.length > 20) state.history.shift();
}

function undo() {
  if (state.history.length < 2) return;

  state.history.pop(); // Remove current state
  const prevState = state.history[state.history.length - 1];

  if (prevState) {
    state.chunks = prevState.chunks;
    state.floatingTexts = prevState.floatingTexts;
    state.annotations = prevState.annotations;
    state.selectedChunks = [];
    rebuildChunks();
    rebuildFloatingTexts();
    render();
    updateChunkCount();
    updateFloatCount();
  }
}

function rebuildChunks() {
  chunksLayer.innerHTML = '';
  state.chunks.forEach(chunk => createChunkElement(chunk));
}

function rebuildFloatingTexts() {
  floatingTextsLayer.innerHTML = '';
  state.floatingTexts.forEach(ft => createFloatingTextElement(ft));
}

function clearAll() {
  if (!confirm('Clear all chunks, labels, and annotations?')) return;

  state.chunks = [];
  state.floatingTexts = [];
  state.annotations = [];
  state.selectedChunks = [];
  chunksLayer.innerHTML = '';
  floatingTextsLayer.innerHTML = '';
  saveHistory();
  render();
  updateChunkCount();
  updateFloatCount();
}

function updateChunkCount() {
  chunkCount.textContent = `Chunks: ${state.chunks.length}`;
}

function cancelAction() {
  state.isDrawing = false;
  selectionBox.style.display = 'none';
  document.getElementById('textInputContainer').classList.add('hidden');
  render();
}

// Panel Functions
function togglePanel(panel) {
  const sidePanel = document.getElementById('sidePanel');
  const aiPanel = document.getElementById('aiPanel');
  const moodPanel = document.getElementById('moodBoardPanel');

  if (sidePanel.classList.contains('hidden')) {
    sidePanel.classList.remove('hidden');
  }

  if (panel === 'ai') {
    aiPanel.classList.remove('hidden');
    moodPanel.classList.add('hidden');
  } else {
    aiPanel.classList.add('hidden');
    moodPanel.classList.remove('hidden');
  }
}

function closePanel() {
  document.getElementById('sidePanel').classList.add('hidden');
}

// AI Functions
function saveApiKey() {
  state.geminiApiKey = document.getElementById('geminiApiKey').value;
  chrome.storage.local.set({ geminiApiKey: state.geminiApiKey });
}

async function generateAISuggestions() {
  const apiKey = document.getElementById('geminiApiKey').value;
  const prompt = document.getElementById('aiPrompt').value;

  if (!apiKey) {
    alert('Please enter your Gemini API key');
    return;
  }

  if (!prompt) {
    alert('Please describe what you want');
    return;
  }

  const loading = document.getElementById('aiLoading');
  const suggestions = document.getElementById('aiSuggestions');
  const btn = document.getElementById('generateSuggestions');

  loading.classList.remove('hidden');
  suggestions.innerHTML = '';
  btn.disabled = true;

  try {
    // Get current layout state
    const layoutData = {
      canvasWidth: canvas.width,
      canvasHeight: canvas.height,
      chunks: state.chunks.map(c => ({
        originalX: c.originalX,
        originalY: c.originalY,
        currentX: c.x,
        currentY: c.y,
        width: c.width,
        height: c.height
      })),
      moodBoardStyles: state.moodBoardImages.length > 0 ? 'User has uploaded mood board images' : 'No mood board'
    };

    const systemPrompt = `You are a UI/UX design expert. The user has a mockup tool where they've cut out UI chunks from a screenshot and want to rearrange them.

Current layout data:
${JSON.stringify(layoutData, null, 2)}

The user wants: ${prompt}

Provide exactly 4 different layout suggestions. For each suggestion:
1. Give it a short name (e.g., "Tight Grid", "Centered Stack")
2. Explain the design principle behind it (2-3 sentences)
3. Describe specific changes (spacing, alignment, grouping)

Format your response as JSON:
{
  "suggestions": [
    {
      "name": "Layout Name",
      "principle": "Design principle explanation",
      "changes": "Specific changes to make"
    }
  ]
}`;

    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: systemPrompt }] }],
        generationConfig: {
          temperature: 0.7,
          maxOutputTokens: 1500
        }
      })
    });

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error.message);
    }

    const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';

    // Parse JSON from response
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      displaySuggestions(parsed.suggestions);
    } else {
      suggestions.innerHTML = `<div class="suggestion-card"><p>${text}</p></div>`;
    }

  } catch (error) {
    console.error('AI Error:', error);
    suggestions.innerHTML = `<div class="suggestion-card"><p style="color:#ef4444">Error: ${error.message}</p></div>`;
  } finally {
    loading.classList.add('hidden');
    btn.disabled = false;
  }
}

function displaySuggestions(suggestionsData) {
  const container = document.getElementById('aiSuggestions');
  container.innerHTML = '';

  suggestionsData.forEach((s, i) => {
    const card = document.createElement('div');
    card.className = 'suggestion-card';
    card.innerHTML = `
      <h4>Option ${i + 1}: ${s.name}</h4>
      <p><strong>Principle:</strong> ${s.principle}</p>
      <p><strong>Changes:</strong> ${s.changes}</p>
    `;
    container.appendChild(card);
  });
}

// Mood Board Functions
function handleMoodBoardUpload(e) {
  const files = e.target.files;

  Array.from(files).forEach(file => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const imgData = event.target.result;
      state.moodBoardImages.push({
        id: 'mood-' + Date.now() + Math.random(),
        data: imgData
      });
      renderMoodBoard();
    };
    reader.readAsDataURL(file);
  });
}

function renderMoodBoard() {
  const grid = document.getElementById('moodBoardGrid');
  grid.innerHTML = '';

  state.moodBoardImages.forEach(img => {
    const item = document.createElement('div');
    item.className = 'mood-item';
    item.innerHTML = `
      <img src="${img.data}" alt="Mood reference">
      <button class="mood-item-delete" data-id="${img.id}">×</button>
    `;
    item.querySelector('.mood-item-delete').addEventListener('click', () => {
      state.moodBoardImages = state.moodBoardImages.filter(m => m.id !== img.id);
      renderMoodBoard();
    });
    grid.appendChild(item);
  });

  // Show/hide style analysis
  const analysis = document.getElementById('styleAnalysis');
  if (state.moodBoardImages.length > 0) {
    analysis.classList.remove('hidden');
    document.getElementById('styleDetails').innerHTML = `
      <div class="style-detail">
        <span class="label">Images uploaded:</span>
        <span class="value">${state.moodBoardImages.length}</span>
      </div>
      <div class="style-detail">
        <span class="label">Status:</span>
        <span class="value">Ready for AI analysis</span>
      </div>
    `;
  } else {
    analysis.classList.add('hidden');
  }
}

// Export Function
async function exportImage() {
  statusText.textContent = 'Exporting...';

  // Create export canvas
  const exportCanvas = document.createElement('canvas');
  exportCanvas.width = canvas.width;
  exportCanvas.height = canvas.height;
  const exportCtx = exportCanvas.getContext('2d');

  // Draw base with filled holes
  exportCtx.drawImage(canvas, 0, 0);

  // Draw chunks at their new positions
  for (const chunk of state.chunks) {
    const img = new Image();
    await new Promise(resolve => {
      img.onload = resolve;
      img.src = chunk.imageData;
    });
    exportCtx.drawImage(img, chunk.x, chunk.y, chunk.width, chunk.height);
  }

  // Draw floating text labels
  state.floatingTexts.forEach(ft => {
    exportCtx.font = 'bold 14px -apple-system, sans-serif';
    exportCtx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    const textWidth = exportCtx.measureText(ft.text).width;
    exportCtx.fillRect(ft.x - 6, ft.y - 16, textWidth + 24, 28);
    exportCtx.strokeStyle = ft.color;
    exportCtx.lineWidth = 2;
    exportCtx.strokeRect(ft.x - 6, ft.y - 16, textWidth + 24, 28);
    exportCtx.fillStyle = ft.color;
    exportCtx.fillText(ft.text, ft.x + 6, ft.y + 4);
  });

  // Create download
  const dataUrl = exportCanvas.toDataURL('image/png');
  const filename = `ui-shuffle-mockup-${Date.now()}.png`;

  // Use chrome downloads API
  chrome.runtime.sendMessage({
    action: 'download',
    dataUrl: dataUrl,
    filename: filename
  });

  statusText.textContent = 'Exported! Check your downloads.';
}

// Handle window resize to reposition elements
window.addEventListener('resize', () => {
  updateCanvasOffset();
  rebuildChunks();
  rebuildFloatingTexts();
});

// Start
init();
