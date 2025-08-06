// Маскировка телефона +7-XXX-XXX-XX-XX
document.addEventListener('DOMContentLoaded', function() {
    // Находим все поля с классом phone-mask
    const phoneInputs = document.querySelectorAll('.phone-mask');
    
    phoneInputs.forEach(function(input) {
        // Применяем маску при вводе
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, ''); // Убираем все нецифровые символы
            
            // Ограничиваем длину 11 цифрами
            if (value.length > 11) {
                value = value.substring(0, 11);
            }
            
            // Форматируем номер
            let formatted = '';
            if (value.length > 0) {
                formatted = '+7';
                if (value.length > 1) {
                    formatted += '-' + value.substring(1, 4);
                }
                if (value.length > 4) {
                    formatted += '-' + value.substring(4, 7);
                }
                if (value.length > 7) {
                    formatted += '-' + value.substring(7, 9);
                }
                if (value.length > 9) {
                    formatted += '-' + value.substring(9, 11);
                }
            }
            
            e.target.value = formatted;
        });
        
        // При фокусе очищаем поле если оно пустое или содержит placeholder
        input.addEventListener('focus', function(e) {
            if (e.target.value === '' || e.target.value === '+7-XXX-XXX-XX-XX') {
                e.target.value = '+7';
            }
        });
        
        // При потере фокуса проверяем валидность
        input.addEventListener('blur', function(e) {
            const value = e.target.value;
            const cleanValue = value.replace(/\D/g, '');
            
            if (cleanValue.length < 11) {
                e.target.classList.add('error');
                if (e.target.nextElementSibling && e.target.nextElementSibling.classList.contains('error-message')) {
                    e.target.nextElementSibling.textContent = 'Номер должен содержать 11 цифр';
                }
            } else {
                e.target.classList.remove('error');
                if (e.target.nextElementSibling && e.target.nextElementSibling.classList.contains('error-message')) {
                    e.target.nextElementSibling.textContent = '';
                }
            }
        });
        
        // При вставке из буфера обмена
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const cleanValue = pastedText.replace(/\D/g, '');
            
            if (cleanValue.length <= 11) {
                input.value = cleanValue;
                input.dispatchEvent(new Event('input'));
            }
        });
    });
});

// Функция для валидации телефона
function validatePhone(phone) {
    const cleanValue = phone.replace(/\D/g, '');
    return cleanValue.length === 11 && cleanValue.startsWith('7');
}

// Функция для форматирования телефона
function formatPhone(phone) {
    const cleanValue = phone.replace(/\D/g, '');
    if (cleanValue.length === 11 && cleanValue.startsWith('7')) {
        return `+7-${cleanValue.substring(1, 4)}-${cleanValue.substring(4, 7)}-${cleanValue.substring(7, 9)}-${cleanValue.substring(9, 11)}`;
    }
    return phone;
} 