// ==========================================
// CARRITO DE MARCO SPORT
// ==========================================

let carrito = [];

try {

    carrito = JSON.parse(
        sessionStorage.getItem(
            "marcoSportCarrito"
        ) || "[]"
    );

    if (!Array.isArray(carrito)) {
        carrito = [];
    }

} catch (error) {

    carrito = [];

}


// ==========================================
// GUARDAR CARRITO
// ==========================================

function guardarCarrito() {

    sessionStorage.setItem(
        "marcoSportCarrito",
        JSON.stringify(carrito)
    );

}


// ==========================================
// ABRIR CARRITO
// ==========================================

function abrirCarrito() {

    const fondo =
        document.getElementById(
            "fondo-carrito"
        );

    const panel =
        document.getElementById(
            "carrito-panel"
        );

    if (fondo) {

        fondo.classList.add(
            "activo"
        );

    }

    if (panel) {

        panel.classList.add(
            "activo"
        );

    }

    actualizarCarrito();

}


// ==========================================
// CERRAR CARRITO
// ==========================================

function cerrarCarrito() {

    const fondo =
        document.getElementById(
            "fondo-carrito"
        );

    const panel =
        document.getElementById(
            "carrito-panel"
        );

    if (fondo) {

        fondo.classList.remove(
            "activo"
        );

    }

    if (panel) {

        panel.classList.remove(
            "activo"
        );

    }

}


// ==========================================
// AGREGAR AL CARRITO
// ==========================================

function agregarAlCarrito(
    modelo,
    precio,
    idTalla
) {

    const selector =
        document.getElementById(
            idTalla
        );

    if (!selector) {

        console.error(
            "No se encontró el selector de talla:",
            idTalla
        );

        return;

    }

    const talla =
        selector.value;

    if (!talla) {

        alert(
            "Selecciona una talla."
        );

        return;

    }

    const existente =
        carrito.find(
            producto =>
                producto.modelo === modelo &&
                String(producto.talla) ===
                String(talla)
        );

    if (existente) {

        existente.cantidad += 1;

    } else {

        carrito.push({

            modelo: modelo,

            precio: precio,

            talla: talla,

            cantidad: 1

        });

    }

    guardarCarrito();

    actualizarCarrito();

    abrirCarrito();

}


// ==========================================
// ACTUALIZAR CARRITO
// ==========================================

function actualizarCarrito() {

    const contenido =
        document.getElementById(
            "contenido-carrito"
        );

    const totalElemento =
        document.getElementById(
            "total-carrito"
        );

    const cantidadElemento =
        document.getElementById(
            "cantidad-carrito"
        );

    if (!contenido) {

        return;

    }


    if (carrito.length === 0) {

        contenido.innerHTML = `
            <div class="carrito-vacio">
                Tu carrito está vacío.
            </div>
        `;

        if (totalElemento) {

            totalElemento.innerText =
                "Total: $0";

        }

        if (cantidadElemento) {

            cantidadElemento.innerText =
                "0";

        }

        return;

    }


    let html = "";

    let total = 0;

    let cantidadTotal = 0;


    carrito.forEach(
        (producto, indice) => {

            const precioNumero =
                convertirPrecio(
                    producto.precio
                );

            const subtotal =
                precioNumero *
                producto.cantidad;

            total += subtotal;

            cantidadTotal +=
                producto.cantidad;


            html += `
                <div class="item-carrito">

                    <strong>
                        ${escapeHtml(
                            producto.modelo
                        )}
                    </strong>

                    <div>
                        Talla ${escapeHtml(
                            producto.talla
                        )}
                    </div>

                    <div>
                        $${formatearPrecio(
                            precioNumero
                        )}
                    </div>

                    <div class="controles-cantidad">

                        <button
                            type="button"
                            onclick="cambiarCantidad(
                                ${indice},
                                -1
                            )"
                        >
                            −
                        </button>

                        <span>
                            ${producto.cantidad}
                        </span>

                        <button
                            type="button"
                            onclick="cambiarCantidad(
                                ${indice},
                                1
                            )"
                        >
                            +
                        </button>

                        <button
                            type="button"
                            onclick="eliminarDelCarrito(
                                ${indice}
                            )"
                        >
                            🗑️
                        </button>

                    </div>

                </div>
            `;

        }
    );


    contenido.innerHTML =
        html;


    if (totalElemento) {

        totalElemento.innerText =
            "Total: $" +
            formatearPrecio(
                total
            );

    }


    if (cantidadElemento) {

        cantidadElemento.innerText =
            cantidadTotal;

    }

}


// ==========================================
// CAMBIAR CANTIDAD
// ==========================================

function cambiarCantidad(
    indice,
    cambio
) {

    if (!carrito[indice]) {

        return;

    }

    carrito[indice].cantidad +=
        cambio;


    if (
        carrito[indice].cantidad <= 0
    ) {

        carrito.splice(
            indice,
            1
        );

    }


    guardarCarrito();

    actualizarCarrito();

}


// ==========================================
// ELIMINAR DEL CARRITO
// ==========================================

function eliminarDelCarrito(
    indice
) {

    if (!carrito[indice]) {

        return;

    }

    carrito.splice(
        indice,
        1
    );

    guardarCarrito();

    actualizarCarrito();

}


// ==========================================
// CONVERTIR PRECIO
// ==========================================

function convertirPrecio(
    precio
) {

    const texto =
        String(
            precio || ""
        );

    const numeros =
        texto.replace(
            /\D/g,
            ""
        );

    return Number(
        numeros || 0
    );

}


// ==========================================
// FORMATEAR PRECIO
// ==========================================

function formatearPrecio(
    numero
) {

    return Number(
        numero || 0
    ).toLocaleString(
        "es-CO"
    );

}


// ==========================================
// SEGURIDAD PARA TEXTO HTML
// ==========================================

function escapeHtml(
    texto
) {

    const elemento =
        document.createElement(
            "div"
        );

    elemento.textContent =
        String(
            texto || ""
        );

    return elemento.innerHTML;

}


// ==========================================
// ENVIAR PEDIDO POR WHATSAPP
// ==========================================

function enviarPedido() {

    if (
        carrito.length === 0
    ) {

        alert(
            "Tu carrito está vacío."
        );

        return;

    }


    let mensaje =
        "Hola, quiero comprar:%0A%0A";


    carrito.forEach(
        producto => {

            mensaje +=
                "• " +
                producto.modelo +
                " - Talla " +
                producto.talla +
                " x" +
                producto.cantidad +
                "%0A";

        }
    );


    const total =
        carrito.reduce(
            (
                suma,
                producto
            ) => {

                return suma +
                    (
                        convertirPrecio(
                            producto.precio
                        ) *
                        producto.cantidad
                    );

            },
            0
        );


    mensaje +=
        "%0ATotal: $" +
        formatearPrecio(
            total
        );


    const numeroWhatsApp =
        "573147611049";


    const url =
        "https://wa.me/" +
        numeroWhatsApp +
        "?text=" +
        mensaje;


    window.open(
        url,
        "_blank"
    );


    carrito = [];

    guardarCarrito();

    actualizarCarrito();

    cerrarCarrito();

}


// ==========================================
// AL CARGAR LA PÁGINA
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        actualizarCarrito();

    }
);