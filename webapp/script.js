// ========== TELEGRAM WEB APP INITIALIZATION ==========
let tg;
try {
    tg = window.Telegram?.WebApp;
} catch (error) {
    console.warn('Telegram WebApp not available, running in browser mode');
}

// ========== GLOBAL VARIABLES ==========
let currentActivity = '';
let formData = {};
let photoFile = null;
let totalSteps = 15;
let isSubmitting = false;

// ========== APP INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Konfigurasi Telegram Web App
    if (tg) {
        tg.ready();
        tg.expand();

        // Ganti warna header mini‑app ke merah agar serasi
        if (tg.setHeaderColor) {
            tg.setHeaderColor('#dc2626');
        }
        if (tg.setBackgroundColor) {
            tg.setBackgroundColor('#F9FAFB');
        }
        if (tg.backgroundColor) {
            document.body.style.backgroundColor = tg.backgroundColor;
        }
        tg.onEvent('viewportChanged', handleViewportChange);
    }

    // Hapus set nilai default tanggal agar progress mulai 0%
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading');
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
            loadingScreen.style.display = 'none';
            const app = document.getElementById('app');
            app.style.display = 'block';
            app.classList.add('fade-in');
        }, 500);
    }, 2000);

    setupEventListeners();
    applyTelegramTheme();
    // Tidak mengisi tanggal otomatis: biarkan user memilih, progress mulai 0

    console.log('🚀 RLEGS Data Entry App - Initialized Successfully!');
}

function setupEventListeners() {
    const form = document.getElementById('dataForm');
    const inputs = form.querySelectorAll('input, select');

    // Validasi dan perbarui progress
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
            updateProgress();
        });
        input.addEventListener('input', function() {
            clearError(this);
            updateProgress();
        });
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
            this.style.transform = 'scale(1.01)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });

    document.getElementById('foto_evidence').addEventListener('change', handlePhotoUpload);
    form.addEventListener('submit', handleFormSubmit);

    // Hindari zoom double tap (iOS)
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);

    document.documentElement.style.scrollBehavior = 'smooth';
}

function handleViewportChange() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}

function applyTelegramTheme() {
    if (!tg) return;
    const root = document.documentElement;
    if (tg.colorScheme === 'dark') {
        root.style.setProperty('--bg-color', tg.backgroundColor || '#1F2937');
        root.style.setProperty('--text-color', tg.textColor || '#FFFFFF');
        root.style.setProperty('--hint-color', tg.hintColor || '#9CA3AF');
    }
}

// ========== ACTIVITY SELECTION ==========
function selectActivity(activity) {
    if (isSubmitting) return;
    currentActivity = activity;
    hapticFeedback('medium');

    const kegiatanSelect = document.getElementById('kegiatan');
    if (kegiatanSelect) {
        kegiatanSelect.value = activity;
    }

    const visitFields = document.getElementById('visitFields');
    const dealingFields = document.getElementById('dealingFields');
    visitFields.style.display = 'none';
    dealingFields.style.display = 'none';

    if (activity === 'Visit') {
        setTimeout(() => {
            visitFields.style.display = 'block';
            visitFields.classList.add('slide-up');
        }, 100);
        setFieldRequirements('visit');
    } else {
        setTimeout(() => {
            dealingFields.style.display = 'block';
            dealingFields.classList.add('slide-up');
        }, 100);
        setFieldRequirements('dealing');
    }

    const mainMenu = document.getElementById('mainMenu');
    const formContainer = document.getElementById('formContainer');
    mainMenu.style.transition = 'all 0.3s ease';
    mainMenu.style.transform = 'translateY(-20px)';
    mainMenu.style.opacity = '0';
    setTimeout(() => {
        mainMenu.style.display = 'none';
        formContainer.style.display = 'block';
        setTimeout(() => {
            formContainer.classList.add('slide-up');
            const formTitle = document.getElementById('formTitle');
            formTitle.textContent = `FORM ${activity.toUpperCase()}`;
            formTitle.classList.add('slide-down');
            updateProgress();
            if (tg?.BackButton) {
                tg.BackButton.show();
                tg.BackButton.onClick(backToMenu);
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }, 50);
    }, 300);
}

function setFieldRequirements(activityType) {
    if (activityType === 'visit') {
        document.getElementById('layanan').required = true;
        document.getElementById('tarif').required = true;
        document.getElementById('paket_deal').required = false;
        document.getElementById('deal_bundling').required = false;
    } else {
        document.getElementById('paket_deal').required = true;
        document.getElementById('deal_bundling').required = true;
        document.getElementById('layanan').required = false;
        document.getElementById('tarif').required = false;
    }
}

function backToMenu() {
    if (isSubmitting) return;
    hapticFeedback('light');

    // Pastikan modal ditutup terlebih dahulu agar overlay tidak tersisa
    const modal = document.getElementById('messageModal');
    if (modal) {
        modal.style.display = 'none';
    }

    const form = document.getElementById('dataForm');
    form.style.transition = 'all 0.3s ease';
    form.style.opacity = '0.5';
    form.style.transform = 'scale(0.98)';
    setTimeout(() => {
        form.reset();
        clearAllErrors();
        removePhoto();
        form.style.opacity = '1';
        form.style.transform = 'scale(1)';
    }, 200);

    const mainMenu = document.getElementById('mainMenu');
    const formContainer = document.getElementById('formContainer');
    formContainer.style.transition = 'all 0.3s ease';
    formContainer.style.transform = 'translateY(20px)';
    formContainer.style.opacity = '0';
    setTimeout(() => {
        formContainer.style.display = 'none';
        mainMenu.style.display = 'block';
        setTimeout(() => {
            mainMenu.style.transform = 'translateY(0)';
            mainMenu.style.opacity = '1';
            mainMenu.classList.add('fade-in');
        }, 50);
        if (tg?.BackButton) {
            tg.BackButton.hide();
        }
        currentActivity = '';
        formData = {};
        photoFile = null;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 300);
}

// ========== PROGRESS MANAGEMENT ==========
function updateProgress() {
    const form = document.getElementById('dataForm');
    const requiredFields = form.querySelectorAll('[required]');
    let filledFields = 0;
    requiredFields.forEach(field => {
        if (field.type === 'file') {
            if (photoFile) filledFields++;
        } else if (field.value.trim() !== '') {
            filledFields++;
        }
    });
    const progress = Math.round((filledFields / requiredFields.length) * 100);
    const progressFill = document.getElementById('progressFill');
    const progressPercent = document.getElementById('progressPercent');
    const currentStep = document.getElementById('currentStep');
    const totalStepsEl = document.getElementById('totalSteps');

    progressFill.style.width = `${progress}%`;
    progressPercent.textContent = `${progress}%`;
    currentStep.textContent = filledFields;
    totalStepsEl.textContent = requiredFields.length;

    if (progress >= 100) {
        progressFill.style.background = 'var(--gradient-success)';
        progressPercent.style.color = 'var(--accent-green)';
        hapticFeedback('medium');
    } else if (progress >= 75) {
        progressFill.style.background = 'var(--gradient-secondary)';
        progressPercent.style.color = 'var(--primary-yellow)';
    } else {
        progressFill.style.background = 'var(--gradient-primary)';
        progressPercent.style.color = 'var(--primary-orange)';
    }

    progressFill.style.animation = 'pulse 0.3s ease';
    setTimeout(() => {
        progressFill.style.animation = '';
    }, 300);
}

// ========== VALIDASI FIELD ==========
function validateField(field) {
    const fieldName = field.name;
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';

    if (field.required && !value) {
        isValid = false;
        errorMessage = 'Field ini wajib diisi';
    } else if (value) {
        switch (fieldName) {
            case 'kode_sa':
                if (!/^[A-Za-z0-9]{3,10}$/.test(value)) {
                    isValid = false;
                    errorMessage = 'Kode SA: 3-10 karakter alfanumerik';
                }
                break;
            case 'nama':
            case 'nama_pic':
            case 'jabatan_pic':
                if (value.length < 2) {
                    isValid = false;
                    errorMessage = 'Minimal 2 karakter';
                } else if (!/^[a-zA-Z\s.,-]+$/.test(value)) {
                    isValid = false;
                    errorMessage = 'Hanya boleh huruf, spasi, titik, koma, dan tanda hubung';
                }
                break;
            case 'no_telp':
            case 'telepon_pic':
                const cleanNumber = value.replace(/[\\s\\-\\+]/g, '');
                if (!/^(62|0)[0-9]{9,13}$/.test(cleanNumber)) {
                    isValid = false;
                    errorMessage = 'Format: 08xxxxxxxxx atau 62xxxxxxxxx';
                }
                break;
            case 'telda':
            case 'tenant':
                if (value.length < 3) {
                    isValid = false;
                    errorMessage = 'Minimal 3 karakter';
                } else if (value.length > 100) {
                    isValid = false;
                    errorMessage = 'Maksimal 100 karakter';
                }
                break;
            case 'tanggal':
                const selectedDate = new Date(value);
                const today = new Date();
                const oneYearAgo = new Date();
                oneYearAgo.setFullYear(today.getFullYear() - 1);
                if (selectedDate > today) {
                    isValid = false;
                    errorMessage = 'Tanggal tidak boleh di masa depan';
                } else if (selectedDate < oneYearAgo) {
                    isValid = false;
                    errorMessage = 'Tanggal terlalu lama (maksimal 1 tahun lalu)';
                }
                break;
        }
    }
    updateFieldAppearance(field, isValid, errorMessage);
    return isValid;
}

function updateFieldAppearance(field, isValid, errorMessage = '') {
    const errorElement = document.getElementById(`error_${field.name}`);
    field.classList.remove('error', 'valid');
    if (field.value.trim() === '') {
        if (errorElement) errorElement.classList.remove('show');
    } else if (isValid) {
        field.classList.add('valid');
        if (errorElement) errorElement.classList.remove('show');
        field.style.transform = 'scale(1.02)';
        field.style.transition = 'all 0.15s ease';
        setTimeout(() => {
            field.style.transform = 'scale(1)';
        }, 150);
    } else {
        field.classList.add('error');
        if (errorElement) {
            errorElement.textContent = errorMessage;
            errorElement.classList.add('show');
        }
        field.style.animation = 'shake 0.3s ease-in-out';
        setTimeout(() => {
            field.style.animation = '';
        }, 300);
        hapticFeedback('heavy');
    }
}

function clearError(field) {
    const errorElement = document.getElementById(`error_${field.name}`);
    field.classList.remove('error');
    if (errorElement) errorElement.classList.remove('show');
}

function clearAllErrors() {
    const errorElements = document.querySelectorAll('.error-msg');
    const inputElements = document.querySelectorAll('input, select');
    errorElements.forEach(error => error.classList.remove('show'));
    inputElements.forEach(input => input.classList.remove('error', 'valid'));
}

// ========== PHOTO HANDLING ==========
function handlePhotoUpload(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('photoPreview');
    const previewImg = document.getElementById('previewImg');
    const uploadPrompt = document.getElementById('uploadPrompt');
    const errorElement = document.getElementById('error_foto_evidence');
    if (!file) return;

    const maxSize = 5 * 1024 * 1024;
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showError(errorElement, 'Format file tidak didukung. Gunakan JPG, PNG, JPEG atau WebP');
        event.target.value = '';
        return;
    }
    if (file.size > maxSize) {
        showError(errorElement, 'Ukuran file terlalu besar. Maksimal 5MB');
        event.target.value = '';
        return;
    }

    clearError(event.target);
    const reader = new FileReader();
    reader.onload = function(e) {
        uploadPrompt.style.transition = 'all 0.3s ease';
        uploadPrompt.style.opacity = '0';
        uploadPrompt.style.transform = 'scale(0.9)';
        setTimeout(() => {
            uploadPrompt.style.display = 'none';
            previewImg.src = e.target.result;
            preview.style.display = 'block';
            preview.style.opacity = '0';
            preview.style.transform = 'scale(0.9)';
            setTimeout(() => {
                preview.style.transition = 'all 0.3s ease';
                preview.style.opacity = '1';
                preview.style.transform = 'scale(1)';
            }, 50);
        }, 300);
        photoFile = file;
        updateProgress();
        hapticFeedback('medium');
    };
    reader.onerror = function() {
        showError(errorElement, 'Gagal membaca file. Coba lagi');
        event.target.value = '';
    };
    reader.readAsDataURL(file);
}

function removePhoto(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const preview = document.getElementById('photoPreview');
    const uploadPrompt = document.getElementById('uploadPrompt');
    const fileInput = document.getElementById('foto_evidence');
    preview.style.transition = 'all 0.3s ease';
    preview.style.opacity = '0';
    preview.style.transform = 'scale(0.9)';
    setTimeout(() => {
        preview.style.display = 'none';
        uploadPrompt.style.display = 'flex';
        uploadPrompt.style.opacity = '0';
        uploadPrompt.style.transform = 'scale(0.9)';
        setTimeout(() => {
            uploadPrompt.style.transition = 'all 0.3s ease';
            uploadPrompt.style.opacity = '1';
            uploadPrompt.style.transform = 'scale(1)';
        }, 50);
    }, 300);
    fileInput.value = '';
    photoFile = null;
    updateProgress();
    hapticFeedback('light');
}

function showError(errorElement, message) {
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
}

// ========== FORM SUBMISSION ==========
function handleFormSubmit(event) {
    event.preventDefault();
    if (isSubmitting) return;

    const form = event.target;
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isFormValid = true;
    inputs.forEach(input => {
        if (!validateField(input)) {
            isFormValid = false;
        }
    });
    if (!isFormValid) {
        showModal('❌', 'Validasi Gagal', 'Mohon perbaiki kesalahan pada form sebelum submit.');
        const firstError = form.querySelector('.error');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        hapticFeedback('heavy');
        return;
    }

    isSubmitting = true;
    const submitButton = document.getElementById('submitButton');
    const btnText = submitButton.querySelector('.btn-text');
    const btnLoader = submitButton.querySelector('.btn-loader');
    submitButton.disabled = true;
    submitButton.style.transform = 'scale(0.98)';
    btnText.style.opacity = '0';
    setTimeout(() => {
        btnText.style.display = 'none';
        btnLoader.style.display = 'block';
        btnLoader.style.opacity = '1';
        submitButton.style.transform = 'scale(1)';
    }, 150);

    setTimeout(() => {
        submitData(form);
    }, 2000);
    hapticFeedback('medium');
}

async function submitData(form) {

	payload = new FormData(form);
	console.log("payload:", payload);
	var isSuccess;

	try {
		const res = await fetch('/api/append-to-sheet', { method: 'POST', body: payload });
		const text = await res.json();
		if (!res.ok)
			throw new Error(text);

		console.log(text);

		isSuccess = res.status;

	} catch (err) {
		console.log(String(err));
	}

    setTimeout(() => {
        isSubmitting = false;
        const submitButton = document.getElementById('submitButton');
        const btnText = submitButton.querySelector('.btn-text');
        const btnLoader = submitButton.querySelector('.btn-loader');
        btnLoader.style.opacity = '0';
        setTimeout(() => {
            btnLoader.style.display = 'none';
            btnText.style.display = 'block';
            btnText.style.opacity = '1';
            submitButton.disabled = false;
        }, 200);
        if (isSuccess) {
            showModal('✅', 'Data Berhasil Disimpan!', `Data ${currentActivity} telah berhasil disimpan ke sistem RLEGS.`);
            hapticFeedback('success');
        } else {
            showModal('❌', 'Submit Gagal', 'Terjadi kesalahan saat menyimpan data. Silakan coba lagi.');
            hapticFeedback('heavy');
        }
    }, 1000);
}

// ========== MODAL HANDLING ==========
function showModal(icon, title, message) {
    const modal = document.getElementById('messageModal');
    const modalIcon = document.getElementById('modalIcon');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    modalIcon.textContent = icon;
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    modal.style.display = 'flex';
    modal.style.opacity = '0';
    setTimeout(() => {
        modal.style.opacity = '1';
    }, 50);
}

// ========== HAPTIC FEEDBACK ==========
function hapticFeedback(type) {
    if (!tg?.HapticFeedback) return;
    try {
        switch (type) {
            case 'light':
                tg.HapticFeedback.impactOccurred('light');
                break;
            case 'medium':
                tg.HapticFeedback.impactOccurred('medium');
                break;
            case 'heavy':
                tg.HapticFeedback.impactOccurred('heavy');
                break;
            case 'success':
                tg.HapticFeedback.notificationOccurred('success');
                break;
            case 'error':
                tg.HapticFeedback.notificationOccurred('error');
                break;
            default:
                tg.HapticFeedback.impactOccurred('light');
        }
    } catch (error) {
        console.warn('Haptic feedback not available:', error);
    }
}

// ========== UTILITAS ==========
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function smoothScrollToElement(element, offset = 0) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

function logPerformance(action) {
    if (typeof performance !== 'undefined' && performance.now) {
        console.log(`${action} at ${performance.now().toFixed(2)}ms`);
    }
}

window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Global error:', {
        message: msg,
        source: url,
        line: lineNo,
        column: columnNo,
        error: error
    });
    if (isSubmitting) {
        isSubmitting = false;
        showModal('❌', 'Terjadi Kesalahan', 'Aplikasi mengalami masalah. Silakan refresh halaman.');
    }
    return false;
};

console.log(`
🚀 RLEGS Data Entry System
📊 Version: 2.0.0
🎯 Status: Ready
💡 Tips: Check console for debug info
`);

window.RLEGS = {
    currentActivity,
    formData: window.formData,
    photoFile,
    isSubmitting,
    hapticFeedback,
    updateProgress,
    validateField
};
