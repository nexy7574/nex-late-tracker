export default async function All(req, res) {
    let response = await fetch("http://localhost:6969/lates/all");
    if(!response.ok) {
        res.status(response.status).json(await response.json());
        return
    }
    const data = await response.json();
    res.status(200).json(data);
}