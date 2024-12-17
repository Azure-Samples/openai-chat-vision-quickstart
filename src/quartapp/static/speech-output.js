class SpeechOutputButton extends HTMLElement {
  static observedAttributes = ["text"];

  constructor() {
    super();
    this.isPlaying = false;
    const SpeechSynthesis =
      window.speechSynthesis || window.webkitSpeechSynthesis;
    if (!SpeechSynthesis) {
      this.dispatchEvent(
        new CustomEvent("speech-output-error", {
          detail: { error: "SpeechSynthesis not supported" },
        })
      );
      return;
    }
    this.synth = SpeechSynthesis;
    this.lngCode = navigator.language || navigator.userLanguage;
  }

  connectedCallback() {
    this.innerHTML = `
            <button class="btn btn-outline-secondary" type="button">
                <i class="bi bi-volume-up"></i>
            </button>`;
    this.speechButton = this.querySelector("button");
    this.speechButton.addEventListener("click", () =>
      this.toggleSpeechOutput()
    );
    document.addEventListener('keydown', this.handleKeydown.bind(this));
  }

  disconnectedCallback() {
    document.removeEventListener('keydown', this.handleKeydown.bind(this));
  }

  handleKeydown(event) {
      if (event.key === 'Escape') {
          this.stopSpeech();
      }
  }

  renderButtonOn() {
    this.speechButton.classList.add("speech-output-active");
    this.speechButton.innerHTML = '<i class="bi bi-volume-up-fill"></i>';
  }

  renderButtonOff() {
    this.speechButton.classList.remove("speech-output-active");
    this.speechButton.innerHTML = '<i class="bi bi-volume-up"></i>';
  }

  toggleSpeechOutput() {
    if (!this.isConnected) {
      return;
    }
    const text = this.getAttribute("text");
    if (this.synth != null) {
      if (this.isPlaying || text === "") {
        this.stopSpeech();
        return;
      }

      // Create a new utterance and play it.
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = this.lngCode;
      utterance.volume = 1;
      utterance.rate = 1;
      utterance.pitch = 1;

      let voice = this.synth
        .getVoices()
        .filter((voice) => voice.lang === this.lngCode)[0];
      if (!voice) {
        voice = this.synth
          .getVoices()
          .filter((voice) => voice.lang === "en-US")[0];
      }
      utterance.voice = voice;

      if (!utterance) {
        return;
      }

      this.synth.speak(utterance);

      utterance.onstart = () => {
        this.isPlaying = true;
        this.renderButtonOn();
      };

      utterance.onend = () => {
        this.isPlaying = false;
        this.renderButtonOff();
      };
    }
  }

  stopSpeech() {
      if (this.synth) {
          this.synth.cancel();
          this.isPlaying = false;
          this.renderButtonOff();
      }
  }
}

customElements.define("speech-output-button", SpeechOutputButton);
