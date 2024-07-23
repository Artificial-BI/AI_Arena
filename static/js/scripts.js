// // voice_input.js

// document.addEventListener('DOMContentLoaded', function() {
//     const voiceInputBtn = document.getElementById('voice-input-btn');
//     const voiceInput = document.getElementById('voice-input');

//     voiceInputBtn.addEventListener('click', function() {
//         const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
//         recognition.lang = 'ru-RU';

//         recognition.onresult = function(event) {
//             const transcript = event.results[0][0].transcript;
//             voiceInput.value += transcript + '\n';
//         };

//         recognition.start();
//     });
// });

// scripts.js

document.addEventListener('DOMContentLoaded', function() {
    function initSlider(sliderId) {
        const slider = document.getElementById(sliderId);
        let currentIndex = 0;
        const slides = slider.getElementsByTagName('img');
        const totalSlides = slides.length;

        function showSlide(index) {
            for (let i = 0; i < totalSlides; i++) {
                slides[i].style.display = 'none';
            }
            slides[index].style.display = 'block';
        }

        function nextSlide() {
            currentIndex = (currentIndex + 1) % totalSlides;
            showSlide(currentIndex);
        }

        function prevSlide() {
            currentIndex = (currentIndex - 1 + totalSlides) % totalSlides;
            showSlide(currentIndex);
        }

        showSlide(currentIndex);

        // Auto slide every 3 seconds
        setInterval(nextSlide, 3000);
    }

    initSlider('arena-slider');
    initSlider('character-slider');
    initSlider('video-slider');
});
function showPopup() {
    document.getElementById('popup').style.display = 'block';
}

function closePopup() {
    document.getElementById('popup').style.display = 'none';
}
