export default async function All(req, res) {
    let body = req.body;
    let fd = new FormData();
    fd.append("minutes_late", body.minutes_late);
    fd.append("excuse", body.excuse);
    let response = await fetch(
        "http://localhost:6969/lates",
        {
            method: "POST",
            body: fd,
            // headers: {
            //     "Content-Type": "application/x-www-form-urlencoded"
            // }
        }
    );
    if(!response.ok) {
        res.status(response.status).json(await response.json());
        return
    }
    const data = await response.json();
    res.status(200).json(data);
}