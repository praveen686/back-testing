import styled from 'styled-components'

let cssDic: { [id: string]: string; } = {};

export const Styler: any = styled.div`
  // making sure css dictionary from earlier element is not carry forwarded
  ${() => { cssDic = {}; return "" }}
  @media (min-width: 0px) {
    ${(props: any) => {
    // only the xs here
    if (props.xs !== undefined) {
      applyStyles(props.xs, cssDic);
      // const finalCssList: string[] = [];
      const finalCssList: string[] = Object.keys(cssDic).map(key => {
        return `${key}:${cssDic[key]};`
      })
      return finalCssList.join("");
    }
    return "";

  }}
  }

  // Small devices (landscape phones, 576px and up) sm
  @media (min-width: 576px) {

  }

  // Medium devices (tablets, 768px and up) md
  @media (min-width: 768px) {

  }

  // Large devices (desktops, 992px and up) lg
  @media (min-width: 992px) {

  }

  // Extra large devices (large desktops, 1200px and up) xl
  @media (min-width: 1200px) {

  }

`
const applyStyles = (cssProps: { [id: string]: string; }, cssDic: { [id: string]: string; }) => {
  Object.keys(cssProps).forEach(key => {
    if (["gtr", "gtc", "gar", "gac"].indexOf(key) > -1) {
      cssDic.display = "grid";
    }
    if (key === "gac") {
      cssDic["grid-auto-flow"] = "column";
      // cssList.push(`grid-auto-flow:column;`)
    }
    if (key === "circle") {
      cssDic["border-radius"] = "50%";
      cssDic["width"] = "10px";
      cssDic["height"] = "10px";
      cssDic["background"] = cssProps[key];
    }
    if (key === "ellipsis") {
      cssDic["white-space"] = "nowrap";
      cssDic["overflow"] = "hidden";
      cssDic["text-overflow"] = "ellipsis";
    }
    if (cssProps[key] !== undefined && styleDic[key] !== undefined) {
      cssDic[styleDic[key]] = cssProps[key];
    }
  })
}


const styleDic: any = {
  d: "display",
  mb: "margin-bottom",
  mt: "margin-top",
  gtr: "grid-template-rows",
  gtc: "grid-template-columns",
  gac: "grid-auto-columns",
  gar: "grid-auto-rows",
  gaf: "grid-auto-flow",
  fs: "font-size",
  als: "align-self",
  jus: "justify-self",
  cg: "column-gap",
  rg: "row-gap",
  br: "border-radius",
  p: "padding",
  pl: "padding-left",
  bdr: "border",
  bb: "border-bottom",
  ai: "align-items",
  mw: "max-width",
  mh: "max-height",
  ht: "height",
  wd: "width",
  bgc: "background-color",
  cr: "cursor",
  bs: "box-sizing",
  ps: "position",
  top: "top",
  gta: "grid-template-areas",
  ga: "grid-area",
  pi: "place-items",
  bdrr: "border-right",
  bxs: "box-shadow"
}


// ${({ gtc }) => {
//   return `${gtc ? `grid-template-columns:${gtc};` : ``}`
// }}
// ${({ gar }) => {
//   return `${gar ? `grid-auto-rows:${gar};` : ``}`
// }}
// ${({ gac }) => {
//   return `${gac ? `grid-auto-columns:${gac};grid-auto-flow:column;` : ``}`
// }}

