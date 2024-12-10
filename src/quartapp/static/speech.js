class SpeechRecordButton extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.shadowRoot.innerHTML = `
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css"
                integrity="sha384-KK94CHFLLe+nY2dmCWGMq91rCGa5gtU4mk92HdvYe+M/SXH301p5ILy+dN9+nJOZ" crossorigin="anonymous">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css"
                integrity="sha256-4RctOgogjPAdwGbwq+rxfwAmSpZhWaafcZR9btzUk18=" crossorigin="anonymous">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootswatch@5.2.3/dist/cosmo/bootstrap.min.css"
                integrity="sha256-axRDISYf7Hht1KhcMnfDV2nq7hD/8Q9Rxa0YlW/o3NU=" crossorigin="anonymous">
            <button class="btn btn-secondary" type="button" id="record-button">
                <i class="bi bi-mic"></i>
            </button>
        `;
        this.isRecording = false;
        this.speechRecognition = this.useCustomSpeechRecognition();
        this.recordButton = this.shadowRoot.getElementById('record-button');
        this.recordButton.addEventListener('click', () => this.toggleRecording());
    }

    useCustomSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.error("SpeechRecognition not supported");
            return null;
        }
        const speechRecognition = new SpeechRecognition();
        speechRecognition.lang = navigator.language || navigator.userLanguage;
        console.log(`Using language: ${speechRecognition.lang}`);
        speechRecognition.interimResults = false;
        speechRecognition.maxAlternatives = 1;
        return speechRecognition;
    }

    startRecording() {
        console.log("Starting speech recognition");
        if (this.speechRecognition == null) {
            console.error("SpeechRecognition not supported");
            return;
        }

        this.speechRecognition.onresult = (event) => {
            let input = "";
            for (const result of event.results) {
                input += result[0].transcript;
            }
            console.log(`Speech recognition result: ${input}`);
            this.dispatchEvent(new CustomEvent('speechresult', { detail: { transcript: input } }));
        };

        this.speechRecognition.onend = () => {
            console.log("Speech recognition ended");
            // NOTE: In some browsers (e.g. Chrome), the recording will stop automatically after a few seconds of silence.
            this.isRecording = false;
            this.recordButton.innerHTML = '<i class="bi bi-mic"></i>';
            this.dispatchEvent(new Event('speechend'));
        };

        this.speechRecognition.onerror = (event) => {
            if (this.speechRecognition) {
                this.speechRecognition.stop();
                if (event.error == "no-speech") {
                    this.dispatchEvent(new CustomEvent('speecherror', { detail: { error: "No speech was detected. Please check your system audio settings and try again." } }));
                } else if (event.error == "language-not-supported") {
                    this.dispatchEvent(new CustomEvent('speecherror', { detail: { error: "The selected language is not supported. Please try a different language." } }));
                } else {
                    this.dispatchEvent(new CustomEvent('speecherror', { detail: { error: "An error occurred while recording. Please try again." } }));
                }
            }
        };

        this.speechRecognition.start();
        this.isRecording = true;
        this.recordButton.innerHTML = '<i class="bi bi-mic-fill"></i>';
    }

    toggleRecording() {
        if (this.isRecording) {
            this.speechRecognition.stop();
        } else {
            this.startRecording();
        }
    }
}

customElements.define('speech-record-button', SpeechRecordButton);
