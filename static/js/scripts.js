// voice_input.js

document.addEventListener('DOMContentLoaded', function() {
    const voiceInputBtn = document.getElementById('voice-input-btn');
    const voiceInput = document.getElementById('voice-input');

    voiceInputBtn.addEventListener('click', function() {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'ru-RU';

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            voiceInput.value += transcript + '\n';
        };

        recognition.start();
    });
});
