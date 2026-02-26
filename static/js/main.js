document.addEventListener('DOMContentLoaded', function () {
    const menuToggle = document.getElementById('menuToggle');
    const navbarMenu = document.getElementById('navbarMenu');
    const dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');

    if (menuToggle && navbarMenu) {
        menuToggle.addEventListener('click', function () {
            navbarMenu.classList.toggle('active');
        });

        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(function (link) {
            link.addEventListener('click', function () {
                navbarMenu.classList.remove('active');
            });
        });
    }

    dropdownToggles.forEach(function (toggle) {
        toggle.addEventListener('click', function () {
            const parentDropdown = this.closest('.nav-dropdown');
            document.querySelectorAll('.nav-dropdown.open').forEach(function (drop) {
                if (drop !== parentDropdown) {
                    drop.classList.remove('open');
                }
            });
            parentDropdown.classList.toggle('open');
        });
    });

    const closeButtons = document.querySelectorAll('.close-alert');
    closeButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            this.parentElement.style.display = 'none';
        });
    });

    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.display = 'none';
        }, 5000);
    });

    initBarcodeScannerButtons();
});

function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function formatarData(data) {
    return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(data));
}

function validarFormulario(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let valido = true;

    inputs.forEach(function (input) {
        if (!input.value.trim()) {
            input.style.borderColor = '#D9534F';
            valido = false;
        } else {
            input.style.borderColor = '';
        }
    });

    return valido;
}

function confirmarDelecao(mensagem) {
    return confirm(mensagem || 'Tem certeza que deseja deletar este item?');
}

function initBarcodeScannerButtons() {
    const buttons = document.querySelectorAll('.js-open-barcode-scanner');
    if (!buttons.length) return;

    let modalState = null;

    buttons.forEach(function (button) {
        button.addEventListener('click', async function () {
            const targetId = this.getAttribute('data-barcode-target');
            const targetInput = document.getElementById(targetId);

            if (!targetInput) {
                alert('Campo de codigo nao encontrado.');
                return;
            }

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert('Seu navegador nao suporta acesso a camera.');
                return;
            }

            if (typeof window.BarcodeDetector === 'undefined') {
                alert('Leitura por camera indisponivel neste navegador. Use Chrome/Edge atualizados.');
                return;
            }

            try {
                const detector = new window.BarcodeDetector({
                    formats: ['ean_13', 'ean_8', 'code_128', 'upc_a', 'upc_e', 'code_39', 'codabar']
                });
                modalState = await openBarcodeScannerModal(targetInput, detector);
            } catch (error) {
                console.error('Erro ao iniciar leitura de codigo:', error);
                alert('Nao foi possivel iniciar a leitura. Verifique permissoes da camera.');
            }
        });
    });

    window.addEventListener('beforeunload', function () {
        if (modalState && typeof modalState.close === 'function') {
            modalState.close();
        }
    });
}

async function openBarcodeScannerModal(targetInput, detector) {
    const modal = document.createElement('div');
    modal.className = 'barcode-scanner-modal active';
    modal.innerHTML = [
        '<div class="barcode-scanner-content">',
        '  <div class="barcode-scanner-header">',
        '    <span class="barcode-scanner-title">Leitura de Codigo de Barras</span>',
        '    <button type="button" class="barcode-scanner-close" aria-label="Fechar">&times;</button>',
        '  </div>',
        '  <div class="barcode-scanner-body">',
        '    <video class="barcode-scanner-video" autoplay playsinline muted></video>',
        '    <p class="barcode-scanner-help">Aponte a camera para o codigo de barras.</p>',
        '  </div>',
        '</div>'
    ].join('');

    document.body.appendChild(modal);

    const video = modal.querySelector('.barcode-scanner-video');
    const closeBtn = modal.querySelector('.barcode-scanner-close');
    let running = true;
    let stream = null;

    const close = function () {
        running = false;
        if (stream) {
            stream.getTracks().forEach(function (track) {
                track.stop();
            });
        }
        modal.remove();
    };

    closeBtn.addEventListener('click', close);
    modal.addEventListener('click', function (event) {
        if (event.target === modal) {
            close();
        }
    });

    stream = await navigator.mediaDevices.getUserMedia({
        video: {
            facingMode: { ideal: 'environment' }
        },
        audio: false
    });

    video.srcObject = stream;

    const scanLoop = async function () {
        if (!running) return;

        try {
            const barcodes = await detector.detect(video);
            if (barcodes && barcodes.length > 0) {
                const rawValue = (barcodes[0].rawValue || '').trim();
                if (rawValue) {
                    targetInput.value = rawValue;
                    targetInput.dispatchEvent(new Event('input', { bubbles: true }));
                    targetInput.dispatchEvent(new Event('change', { bubbles: true }));
                    close();
                    return;
                }
            }
        } catch (error) {
            // Ignora falhas pontuais de detecção por frame.
        }

        setTimeout(scanLoop, 250);
    };

    scanLoop();

    return { close: close };
}