import React from 'react'

import styled from 'styled-components'

const InputBox = styled.input`
  padding: 1rem;
  width: 50%;
  border-radius: 30px;
  margin: 2rem 1rem;
  // 
  background: linear-gradient(45deg, #004D4D, #009999);
  
  color: #fff;
  border: none;
  outline: none;
  // box-shadow: 0 0 4px 4px #424242;
`;

const Input = ({type,placeholder,name,style,value,onChange,onKeyPress}) => {
  return (
    <InputBox
        type={type}
        placeholder={placeholder}
        name={name}
        value={value}
        onChange={onChange}
        onKeyPress={onKeyPress}
        style={style}
         
          />
  )
}

export default Input;