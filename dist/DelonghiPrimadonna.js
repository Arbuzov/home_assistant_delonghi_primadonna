const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

class PlantPictureCard extends HTMLElement {}

export class PlantPictureCardEditor extends LitElement {}

customElements.define("plant-picture-card", PlantPictureCard);
customElements.define("plant-picture-card-editor", PlantPictureCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "plant-picture-card",
  name: "Plant Picture Card",
  preview: true, // Optional - defaults to false
  description: "Like a picture glance card but for plant data" // Optional
});