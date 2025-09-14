const express = require('express');
const app = express();
const http = require('http').createServer(app);
const io = require('socket.io')(http);

// Serve static files (like HTML)
app.use(express.static('public'));

// Handle Socket.IO connections
io.on('connection', (socket) => {
    console.log('A user connected:', socket.id);

    // Join a room
    socket.on('join-room', (roomId) => {
        socket.join(roomId);
        socket.to(roomId).emit('user-connected', socket.id);
        console.log(`${socket.id} joined room ${roomId}`);
    });

    // Handle WebRTC offer
    socket.on('offer', (data) => {
        socket.to(data.roomId).emit('offer', { offer: data.offer, from: socket.id });
    });

    // Handle WebRTC answer
    socket.on('answer', (data) => {
        socket.to(data.roomId).emit('answer', { answer: data.answer, from: socket.id });
    });

    // Handle ICE candidates
    socket.on('ice-candidate', (data) => {
        socket.to(data.roomId).emit('ice-candidate', { candidate: data.candidate, from: socket.id });
    });

    // Handle user disconnect
    socket.on('disconnect', () => {
        console.log('User disconnected:', socket.id);
        io.emit('user-disconnected', socket.id);
    });
});

// Start the server
const PORT = process.env.PORT || 3000;
http.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});