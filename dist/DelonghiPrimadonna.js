const LitElement = Object.getPrototypeOf(customElements.get("ha-panel-lovelace"));
const {html} = LitElement.prototype;
const {css} = LitElement.prototype;

const DEFAULT_IMAGE_URL = "https://delonghibe.s3.eu-west-1.amazonaws.com/cms/prod/img/_opt_delonghi_uploads_PD_CLASS_TOP_INT_ECAM550.85.MS.png";

class DelonghiImageCard extends LitElement {
  static get properties() {
    return { hass: {}, _config: {} };
  }

  setConfig(config) {
    this._config = config;
  }

  render() {
    const image = this._config.image || DEFAULT_IMAGE_URL;
    return html`<ha-card><img class="machine-image" src="${image}" /></ha-card>`;
  }

  static get styles() {
    return css`
      .machine-image {
        width: 100%;
        display: block;
      }
    `;
  }
}

customElements.define("delonghi-image-card", DelonghiImageCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "delonghi-image-card",
  name: "Delonghi Image Card",
  preview: true,
  description: "Card showing Delonghi coffee machine image",
});
