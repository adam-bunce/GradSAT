import { geist_mono } from "../../styles/fonts";

export default function Card({ header, body, image_url }) {
  return (
    <div
      className={
        "text-lg flex flex-col border border-black basic-shadow hover:-translate-y-2 duration-300 break-inside-avoid bg-white cursor-pointer"
      }
    >
      <h6
        className={`border-b border-b-gray-400 p-3 ${geist_mono.className} uppercase`}
      >
        {header}
      </h6>
      <div className={"p-3 text-base flex-grow"}>{body}</div>

      <img src={image_url} alt="not important" className={"opacity-80 mt-8"} />
    </div>
  );
}
