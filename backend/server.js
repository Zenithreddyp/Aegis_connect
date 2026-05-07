import http from "http";
import express from "express";


const app = express();
const server = http.createServer(app);


app.use(cors({ origin: "http://localhost:5173", credentials: true }));
app.use(express.json());


server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
