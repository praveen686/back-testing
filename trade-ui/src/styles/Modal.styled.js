
import styled from 'styled-components'

export const StyledModal = styled.div`
  position:fixed;
  width:100%;
  height:100%;
  top:0px;
  left:0px;
  display:grid;
  align-content:center;
  justify-content:center;
  grid-template-rows: 1fr 1fr 1fr;
  .inner{
      position:relative;
      width:100px;
      height:100px;
  }

`