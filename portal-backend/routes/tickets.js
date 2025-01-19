const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const QRCode = require('qrcode');

// Function to get encryption key (matches Python version)
function getEncryptionKey(password) {
    const salt = Buffer.from('salt_123'); // Same salt as Python
    const keyLength = 32;
    const iterations = 100000;

    return crypto.pbkdf2Sync(
        password,
        salt,
        iterations,
        keyLength,
        'sha256'
    );
}

// Decrypt function
function decrypt(encryptedText, key) {
    try {
        // Convert base64 to buffer
        const combined = Buffer.from(encryptedText, 'base64');
        
        // Extract IV and ciphertext
        const iv = combined.slice(0, 16);
        const ciphertext = combined.slice(16);

        // Create decipher
        const decipher = crypto.createDecipheriv('aes-256-cbc', key, iv);
        
        // Decrypt
        let decrypted = decipher.update(ciphertext);
        decrypted = Buffer.concat([decrypted, decipher.final()]);
        console.log('Decrypted:', decrypted);
        
        return decrypted.toString();
    } catch (error) {
        console.error('Decryption error:', error);
        return null;
    }
}

router.get('/get_ticket', async (req, res) => {
    const { code } = req.query;
    
    if (!code) {
        return res.status(400).send('No code provided');
    }

    // Get encryption key using the same password as Python
    const key = getEncryptionKey('hackers!bruh');
    
    // Decrypt the code
    const decryptedValue = decrypt(code, key);
    console.log('Decrypted value:', decryptedValue);
    if (!decryptedValue) {
        return res.status(400).send('Invalid code');
    }

    // Generate QR code with higher quality
    try {
        const qrCodeDataUrl = await QRCode.toDataURL(decryptedValue, {
            width: 800,
            margin: 2,
            quality: 1.0,
            scale: 8
        });
        
        // Serve HTML page with QR code and modal functionality
        const html = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Ticket QR Code</title>
                <style>
                    body {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                        font-family: Arial, sans-serif;
                        background-color: #f5f5f5;
                    }
                    .qr-container {
                        cursor: pointer;
                        transition: transform 0.2s;
                    }
                    .qr-container:hover {
                        transform: scale(1.02);
                    }
                    .qr-code {
                        max-width: 300px;
                        margin: 20px;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }
                    .modal {
                        display: none;
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background-color: rgba(0,0,0,0.9);
                        z-index: 1000;
                        cursor: pointer;
                    }
                    .modal-content {
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        max-width: 90%;
                        max-height: 90%;
                    }
                    .close {
                        position: absolute;
                        top: 15px;
                        right: 35px;
                        color: #f1f1f1;
                        font-size: 40px;
                        font-weight: bold;
                        cursor: pointer;
                    }
                </style>
            </head>
            <body>
                <h1>Your HackDuke Ticket</h1>
                <div class="qr-container" onclick="openModal()">
                    <img src="${qrCodeDataUrl}" alt="Ticket QR Code" class="qr-code"/>
                </div>

                <div id="qrModal" class="modal" onclick="closeModal()">
                    <span class="close">&times;</span>
                    <img src="${qrCodeDataUrl}" alt="Ticket QR Code" class="modal-content"/>
                </div>

                <script>
                    function openModal() {
                        document.getElementById('qrModal').style.display = 'block';
                    }

                    function closeModal() {
                        document.getElementById('qrModal').style.display = 'none';
                    }

                    // Close modal when pressing escape key
                    document.addEventListener('keydown', function(event) {
                        if (event.key === 'Escape') {
                            closeModal();
                        }
                    });
                </script>
            </body>
            </html>
        `;
        
        res.send(html);
    } catch (error) {
        console.error('QR Code generation error:', error);
        res.status(500).send('Error generating QR code');
    }
});

module.exports = router;
