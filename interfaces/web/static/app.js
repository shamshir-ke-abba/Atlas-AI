const chat = document.getElementById("chat");
const input = document.getElementById("message");
const sendButton = document.getElementById("send");


function addMessage(
    sender,
    text,
    type
) {

    const div =
        document.createElement("div");

    div.className =
        `message ${type}`;

    const senderElement =
        document.createElement("b");

    senderElement.textContent =
        `${sender}: `;

    const textElement =
        document.createElement("span");

    textElement.textContent =
        text;

    div.appendChild(
        senderElement
    );

    div.appendChild(
        textElement
    );

    chat.appendChild(
        div
    );

    chat.scrollTop =
        chat.scrollHeight;

    return textElement;
}


async function sendMessage() {

    const text =
        input.value.trim();

    if (!text)
        return;


    addMessage(
        "You",
        text,
        "user"
    );


    input.value = "";

    sendButton.disabled = true;
    input.disabled = true;


    const responseElement =
        addMessage(
            "Atlas",
            "",
            "atlas"
        );


    try {

        const response =
            await fetch(
                "/stream",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/x-ndjson"
                    },

                    body: JSON.stringify({
                        message: text
                    })
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        if (!response.body) {

            throw new Error(
                "Streaming is unavailable."
            );
        }


        const reader =
            response.body.getReader();

        const decoder =
            new TextDecoder("utf-8");


        let buffer = "";


        while (true) {

            const {
                value,
                done
            } = await reader.read();


            if (done)
                break;


            buffer +=
                decoder.decode(
                    value,
                    {
                        stream: true
                    }
                );


            const lines =
                buffer.split("\n");


            buffer =
                lines.pop() || "";


            for (
                const line of lines
            ) {

                const trimmed =
                    line.trim();


                if (!trimmed)
                    continue;


                let data;


                try {

                    data =
                        JSON.parse(
                            trimmed
                        );

                } catch (error) {

                    console.error(
                        "Invalid stream data:",
                        trimmed
                    );

                    continue;
                }


                // ----------------------------------
                // Backend error
                // ----------------------------------

                if (data.error) {

                    throw new Error(
                        data.error
                    );
                }


                // ----------------------------------
                // Normal chunk
                // ----------------------------------

                if (
                    typeof data.chunk
                    === "string"
                ) {

                    responseElement
                        .textContent +=
                            data.chunk;

                    chat.scrollTop =
                        chat.scrollHeight;
                }
            }
        }


        // Process any final buffered line.

        const finalLine =
            buffer.trim();


        if (finalLine) {

            try {

                const data =
                    JSON.parse(
                        finalLine
                    );


                if (data.error) {

                    throw new Error(
                        data.error
                    );
                }


                if (
                    typeof data.chunk
                    === "string"
                ) {

                    responseElement
                        .textContent +=
                            data.chunk;
                }

            } catch (error) {

                if (
                    error instanceof Error
                    &&
                    error.message !==
                    "Unexpected end of JSON input"
                ) {

                    throw error;
                }
            }
        }


    } catch (error) {

        console.error(
            "Atlas request failed:",
            error
        );


        responseElement.textContent =
            `Error: ${error.message}`;

    } finally {

        sendButton.disabled = false;
        input.disabled = false;

        input.focus();
    }
}


sendButton.addEventListener(
    "click",
    sendMessage
);


input.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter"
            && !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);