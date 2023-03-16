export default async function All(req, res) {
    const [day, month, year] = (req.query.id || "01/01/2022").split("/")
    const response = await fetch(
        `http://localhost:6969/lates/${year}/${month}/${day}`,
        {
            method: "DELETE"
        }
    )
    res.status(response.status).send()
}