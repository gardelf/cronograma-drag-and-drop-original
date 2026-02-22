// Widget de Gastos de Ayer
// Muestra los gastos del día anterior con formato visual

const API_URL = "https://web-production-2ae52.up.railway.app/gastos-ayer";

// Mapeo de categorías a emojis
const CATEGORY_EMOJIS = {
  "Comida": "🍽️",
  "Coche": "🚗",
  "Salud": "💊",
  "Transporte": "🚌",
  "Ocio": "🎮",
  "Ropa": "👕",
  "Casa": "🏠",
  "Tecnología": "💻",
  "Viajes": "✈️",
  "Otros": "📦"
};

// Colores por categoría
const CATEGORY_COLORS = {
  "Comida": Color.orange(),
  "Coche": Color.blue(),
  "Salud": Color.red(),
  "Transporte": Color.purple(),
  "Ocio": Color.green(),
  "Ropa": Color.pink(),
  "Casa": Color.brown(),
  "Tecnología": Color.gray(),
  "Viajes": Color.cyan(),
  "Otros": Color.lightGray()
};

async function fetchGastos() {
  try {
    const req = new Request(API_URL);
    const data = await req.loadJSON();
    return data;
  } catch (error) {
    console.error("Error al obtener gastos:", error);
    return null;
  }
}

function getEmojiForCategory(category) {
  return CATEGORY_EMOJIS[category] || "💰";
}

function getColorForCategory(category) {
  return CATEGORY_COLORS[category] || Color.gray();
}

function createWidget(data) {
  const widget = new ListWidget();
  
  // Fondo degradado
  const gradient = new LinearGradient();
  gradient.colors = [new Color("#1e3a8a"), new Color("#3b82f6")];
  gradient.locations = [0.0, 1.0];
  widget.backgroundGradient = gradient;
  
  widget.setPadding(16, 16, 16, 16);
  
  if (!data || data.count === 0) {
    // Sin gastos
    const noDataText = widget.addText("✅ Sin gastos ayer");
    noDataText.font = Font.boldSystemFont(16);
    noDataText.textColor = Color.white();
    noDataText.centerAlignText();
    return widget;
  }
  
  // Título
  const title = widget.addText("💰 Gastos de ayer");
  title.font = Font.boldSystemFont(14);
  title.textColor = Color.white();
  
  widget.addSpacer(8);
  
  // Total
  const totalStack = widget.addStack();
  totalStack.layoutHorizontally();
  totalStack.centerAlignContent();
  
  const totalText = totalStack.addText(`${data.total.toFixed(2)} ${data.currency}`);
  totalText.font = Font.boldSystemFont(24);
  totalText.textColor = Color.yellow();
  
  totalStack.addSpacer(4);
  
  const countText = totalStack.addText(`(${data.count})`);
  countText.font = Font.systemFont(14);
  countText.textColor = Color.white();
  countText.textOpacity = 0.7;
  
  widget.addSpacer(12);
  
  // Lista de gastos (máximo 4 para que quepa)
  const maxExpenses = Math.min(data.expenses.length, 4);
  
  for (let i = 0; i < maxExpenses; i++) {
    const expense = data.expenses[i];
    
    const expenseStack = widget.addStack();
    expenseStack.layoutHorizontally();
    expenseStack.centerAlignContent();
    
    // Emoji de categoría
    const emoji = expenseStack.addText(getEmojiForCategory(expense.category));
    emoji.font = Font.systemFont(12);
    
    expenseStack.addSpacer(4);
    
    // Descripción (truncada)
    let description = expense.description.replace("€", "").trim();
    if (description.length > 20) {
      description = description.substring(0, 20) + "...";
    }
    
    const descText = expenseStack.addText(description);
    descText.font = Font.systemFont(11);
    descText.textColor = Color.white();
    descText.lineLimit = 1;
    
    expenseStack.addSpacer();
    
    // Monto
    const amountText = expenseStack.addText(`${expense.amount.toFixed(2)}€`);
    amountText.font = Font.boldSystemFont(11);
    amountText.textColor = Color.yellow();
    
    widget.addSpacer(4);
  }
  
  // Si hay más gastos, mostrar indicador
  if (data.expenses.length > maxExpenses) {
    widget.addSpacer(4);
    const moreText = widget.addText(`+${data.expenses.length - maxExpenses} más...`);
    moreText.font = Font.systemFont(10);
    moreText.textColor = Color.white();
    moreText.textOpacity = 0.6;
  }
  
  widget.addSpacer();
  
  // Fecha
  const dateText = widget.addText(`📅 ${data.date}`);
  dateText.font = Font.systemFont(9);
  dateText.textColor = Color.white();
  dateText.textOpacity = 0.5;
  
  return widget;
}

async function run() {
  const data = await fetchGastos();
  const widget = createWidget(data);
  
  if (config.runsInWidget) {
    Script.setWidget(widget);
  } else {
    widget.presentMedium();
  }
  
  Script.complete();
}

await run();
