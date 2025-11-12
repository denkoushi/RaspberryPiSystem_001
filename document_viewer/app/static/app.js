(() => {
  const config = window.DOCVIEWER_CONFIG || {};
  const apiBaseRaw = typeof config.apiBase === 'string' ? config.apiBase.trim() : '';
  const apiBase = apiBaseRaw.endsWith('/') ? apiBaseRaw.slice(0, -1) : apiBaseRaw;
  const apiToken = typeof config.apiToken === 'string' ? config.apiToken.trim() : '';
  const socketBaseRaw = typeof config.socketBase === 'string' ? config.socketBase.trim() : '';
  const socketBase = socketBaseRaw.endsWith('/') ? socketBaseRaw.slice(0, -1) : socketBaseRaw;
  const rawSocketPath = typeof config.socketPath === 'string' ? config.socketPath.trim() : '';
  const socketPath = rawSocketPath ? (rawSocketPath.startsWith('/') ? rawSocketPath : `/${rawSocketPath}`) : '/socket.io';
  const socketAutoOpen = config.socketAutoOpen !== false;
  const normalizeList = (value) => {
    if (!Array.isArray(value)) return [];
    return value
      .map((item) => (typeof item === 'string' ? item.trim() : ''))
      .filter((item) => item.length > 0);
  };
  const acceptDeviceIds = normalizeList(config.acceptDeviceIds);
  const acceptLocationCodes = normalizeList(config.acceptLocationCodes);
  const normalizeSocketEvents = (value) => {
    if (!Array.isArray(value)) return [];
    return value
      .map((item) => (typeof item === 'string' ? item.trim() : ''))
      .filter((item) => item.length > 0);
  };
  const socketEvents = (() => {
    const configured = normalizeSocketEvents(config.socketEvents);
    if (configured.length) {
      return [...new Set(configured)];
    }
    return ['scan.ingested', 'part_location_updated', 'scan_update'];
  })();

  const logSocketEvent = (eventName, payload) => {
    const body = JSON.stringify({ event: eventName, payload });
    const endpoint = buildApiUrl('/api/socket-events');
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    }).catch(() => {});
  };

  const buildApiUrl = (path) => {
    const normalized = path.startsWith('/') ? path : `/${path}`;
    if (!apiBase) {
      return normalized;
    }
    return `${apiBase}${normalized}`;
  };

  const buildHeaders = () => {
    const headers = {
      Accept: 'application/json',
    };
    if (apiToken) {
      headers.Authorization = `Bearer ${apiToken}`;
    }
    return headers;
  };

  const resolveDocumentUrl = (url) => {
    if (!url) {
      return '';
    }
    const absolutePattern = /^(?:[a-z]+:)?\/\//i;
    if (absolutePattern.test(url)) {
      return url;
    }
    if (!apiBase) {
      return url;
    }
    const normalized = url.startsWith('/') ? url : `/${url}`;
    return `${apiBase}${normalized}`;
  };

  const app = document.getElementById('app');
  const barcodeInput = document.getElementById('barcode-input');
  const manualOpenButton = document.getElementById('manual-open');
  const statusIndicator = document.getElementById('status-indicator');
  const viewerPartNumber = document.getElementById('viewer-part-number');
  const viewerFilename = document.getElementById('viewer-filename');
  const pdfFrame = document.getElementById('pdf-frame');
  const returnButton = document.getElementById('return-to-idle');
  const errorResetButton = document.getElementById('error-reset');
  const errorMessage = document.getElementById('error-message');
  const errorTimer = document.getElementById('error-timer');
  const socketStatus = document.getElementById('socket-status');

  let errorTimeoutId = null;
  let countdownIntervalId = null;
  const isEmbedded = window.self !== window.top;
  let currentPartNumber = '';
  let currentFilename = '';
  let socket = null;
  let lastSocketPayload = null;
  let lastSocketKey = null;

  const notifyParent = (state) => {
    if (window.parent && window.parent !== window) {
      try {
        window.parent.postMessage({
          type: 'viewer-state',
          state,
          part: currentPartNumber,
          filename: currentFilename
        }, '*');
      } catch (_) {}
    }
  };

  const socketLabel = {
    live: 'Socket: LIVE',
    connecting: 'Socket: 接続中…',
    offline: 'Socket: OFFLINE',
    disabled: 'Socket: 無効',
    error: 'Socket: エラー',
  };

  const updateSocketStatus = (state, label) => {
    if (!socketStatus) return;
    socketStatus.dataset.state = state;
    socketStatus.textContent = label || socketLabel[state] || 'Socket: -';
  };

  const shouldAcceptDevice = (deviceId) => {
    if (!acceptDeviceIds.length) return true;
    const value = typeof deviceId === 'string' ? deviceId.trim() : '';
    return value ? acceptDeviceIds.includes(value) : false;
  };

  const shouldAcceptLocation = (locationCode) => {
    if (!acceptLocationCodes.length) return true;
    const value = typeof locationCode === 'string' ? locationCode.trim() : '';
    return value ? acceptLocationCodes.includes(value) : false;
  };

  const setState = (state) => {
    app.dataset.state = state;
    app.classList.toggle('scan-ready', state === 'idle');
    switch (state) {
      case 'idle':
        statusIndicator.textContent = '待機中';
        barcodeInput.value = '';
        pdfFrame.src = '';
        viewerPartNumber.textContent = '';
        viewerFilename.textContent = '';
        currentPartNumber = '';
        currentFilename = '';
        clearTimers();
        focusInput();
        break;
      case 'viewer':
        statusIndicator.textContent = '表示中';
        clearTimers();
        break;
      case 'error':
        statusIndicator.textContent = 'エラー';
        break;
      case 'searching':
        statusIndicator.textContent = '検索中…';
        focusInput();
        break;
      default:
        statusIndicator.textContent = '';
    }
    statusIndicator.dataset.state = state;
    ensureFocus();
    notifyParent(state);
  };

  const clearTimers = () => {
    if (errorTimeoutId) {
      clearTimeout(errorTimeoutId);
      errorTimeoutId = null;
    }
    if (countdownIntervalId) {
      clearInterval(countdownIntervalId);
      countdownIntervalId = null;
    }
    errorTimer.textContent = '';
  };

  const focusInput = () => {
    if (!barcodeInput) return;
    try {
      barcodeInput.focus({ preventScroll: true });
    } catch (_) {
      barcodeInput.focus();
    }
  };

  const ensureFocus = () => {
    if (document.activeElement !== barcodeInput) {
      focusInput();
    }
  };

  window.addEventListener('load', () => {
    if (!isEmbedded) {
      ensureFocus();
    } else {
      focusInput();
    }
    setState('idle');
    connectSocket();
  });

  if (!isEmbedded) {
    setInterval(ensureFocus, 1500);
  }

  const lookupDocument = async (partNumber) => {
    const trimmed = partNumber.trim();
    if (!trimmed) {
      return;
    }

    if (window.parent && window.parent !== window) {
      try {
        window.parent.postMessage({ type: 'dv-barcode', part: trimmed, order: '' }, '*');
      } catch (_) {}
    }

    setState('searching');

    try {
      const response = await fetch(buildApiUrl(`/api/documents/${encodeURIComponent(trimmed)}`), {
        headers: buildHeaders(),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({ message: 'document not found' }));
        throw new Error(data.message || 'document not found');
      }

      const data = await response.json();
      currentPartNumber = trimmed;
      currentFilename = data.filename;
      viewerPartNumber.textContent = trimmed;
      viewerFilename.textContent = data.filename;
      const documentUrl = resolveDocumentUrl(data.url);
      pdfFrame.src = documentUrl ? `${documentUrl}#toolbar=1&navpanes=0` : '';
      setState('viewer');
      notifyParent('viewer');
      if (window.parent && window.parent !== window) {
        try {
          window.parent.postMessage({ type: 'dv-barcode', part: trimmed, order: data.order || '' }, '*');
        } catch (_) {}
      }
    } catch (error) {
      console.error(error);
      displayError(trimmed, error.message || '該当資料が見つかりません');
    } finally {
      if (barcodeInput) {
        barcodeInput.value = '';
      }
    }
  };

  const handleSocketPayload = (payload) => {
    if (!payload || typeof payload !== 'object') return;
    lastSocketPayload = payload;

    const part =
      payload.order_code ||
      payload.orderCode ||
      payload.part_number ||
      payload.partNumber ||
      '';

    if (!part || typeof part !== 'string') {
      return;
    }

    const deviceId = payload.device_id || payload.deviceId || '';
    const locationCode = payload.location_code || payload.locationCode || '';
    if (!shouldAcceptDevice(deviceId)) {
      return;
    }
    if (!shouldAcceptLocation(locationCode)) {
      return;
    }

    const scanId = payload.scan_id || payload.scanId || '';
    const updatedAt = payload.updated_at || payload.updatedAt || '';
    const dedupeKey = scanId || (updatedAt ? `${part}#${updatedAt}` : '');
    if (dedupeKey && dedupeKey === lastSocketKey) {
      return;
    }
    if (dedupeKey) {
      lastSocketKey = dedupeKey;
    }

    if (app.dataset.state === 'viewer' && currentPartNumber === part.trim()) {
      return;
    }

    lookupDocument(part);
  };

  const attachSocketListeners = () => {
    if (!socket || typeof socket.on !== 'function') {
      return;
    }
    socket.on('connect', () => {
      updateSocketStatus('live');
    });
    socket.on('disconnect', () => {
      updateSocketStatus('offline');
    });
    socket.on('connect_error', (error) => {
      console.error('Socket connect_error', error);
      updateSocketStatus('error', socketLabel.error);
    });
    socketEvents.forEach((eventName) => {
      socket.on(eventName, (payload) => {
        console.debug('[dv] Socket event', eventName, payload);
        logSocketEvent(eventName, payload);
        handleSocketPayload(payload);
      });
    });
    if (socket.io && typeof socket.io.on === 'function') {
      socket.io.on('reconnect_attempt', () => updateSocketStatus('connecting'));
      socket.io.on('reconnect', () => updateSocketStatus('live'));
      socket.io.on('reconnect_error', () => updateSocketStatus('error', socketLabel.error));
    }
  };

  const connectSocket = () => {
    if (!socketAutoOpen) {
      updateSocketStatus('disabled');
      return;
    }
    if (!socketBase) {
      updateSocketStatus('disabled', 'Socket: 未設定');
      return;
    }
    if (socket && typeof socket.connect === 'function') {
      if (!socket.connected) {
        updateSocketStatus('connecting');
        socket.connect();
      }
      return;
    }
    if (typeof window.io !== 'function') {
      updateSocketStatus('offline', 'Socket: クライアント未ロード');
      return;
    }
    updateSocketStatus('connecting');
    socket = window.io(socketBase, {
      path: socketPath,
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 8000,
    });
    attachSocketListeners();
  };

  const displayError = (partNumber, message) => {
    errorMessage.textContent = `部品番号「${partNumber}」: ${message}`;
    setState('error');
    startErrorCountdown();
  };

  const startErrorCountdown = (seconds = 5) => {
    let remaining = seconds;
    errorTimer.textContent = `${remaining} 秒後に待機画面に戻ります`;

    countdownIntervalId = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        clearTimers();
        setState('idle');
      } else {
        errorTimer.textContent = `${remaining} 秒後に待機画面に戻ります`;
      }
    }, 1000);

    errorTimeoutId = setTimeout(() => {
      clearTimers();
      setState('idle');
    }, seconds * 1000);
  };

  if (barcodeInput) {
    barcodeInput.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        lookupDocument(barcodeInput.value);
      } else if (event.key === 'Escape') {
        event.preventDefault();
        setState('idle');
      }
    });
  }

  if (manualOpenButton) {
    manualOpenButton.addEventListener('click', () => {
      lookupDocument(barcodeInput ? barcodeInput.value : '');
    });
  }

  if (returnButton) {
    returnButton.addEventListener('click', () => {
      setState('idle');
    });
  }

  if (errorResetButton) {
    errorResetButton.addEventListener('click', () => {
      setState('idle');
    });
  }

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      ensureFocus();
    }
  });

  window.addEventListener('click', () => {
    ensureFocus();
  });

  window.addEventListener('message', (event) => {
    const data = event.data;
    if (!data || typeof data !== 'object') return;
    if (data.type === 'focus-request') {
      focusInput();
      return;
    }
    if (data.type === 'viewer-return') {
      setState('idle');
    }
  });
})();
